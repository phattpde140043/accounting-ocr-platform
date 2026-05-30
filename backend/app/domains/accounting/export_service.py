from hashlib import sha256

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_mixins import new_id
from app.domains.accounting.lifecycle import (
    AccountingDocumentStatus,
    AccountingExportBatchStatus,
    can_document_transition,
    can_export_batch_transition,
)
from app.domains.accounting.models import AccountingExportBatch, AccountingExportItem
from app.domains.accounting.repositories import (
    AccountingDocumentRepository,
    AccountingExportBatchRepository,
    AccountingExportItemRepository,
)
from app.domains.accounting.schemas import CreateExportBatchIn
from app.domains.accounting.export_templates import (
    ExportArtifact,
    build_export_artifact,
    normalize_export_template,
)
from app.domains.platform.audit_service import AuditEventCreate, AuditLogService
from app.domains.platform.audit_catalog import DomainEvent


class AccountingExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.documents = AccountingDocumentRepository(session)
        self.batches = AccountingExportBatchRepository(session)
        self.items = AccountingExportItemRepository(session)
        self.audit_log = AuditLogService(session)

    async def create_export_batch(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        payload: CreateExportBatchIn,
    ) -> dict:
        export_template = normalize_export_template(payload.format)
        idempotency_key = build_export_idempotency_key(
            document_ids=payload.document_ids,
            export_format=export_template.value,
            requested_key=payload.idempotency_key,
        )
        existing_batch = await self.batches.get_by_idempotency_key(
            organization_id, idempotency_key
        )
        if existing_batch is not None:
            existing_items = await self.items.list_for_batch(
                organization_id, existing_batch.id
            )
            return {
                "id": existing_batch.id,
                "status": existing_batch.status,
                "format": existing_batch.format,
                "document_count": len(existing_items),
            }

        document_ids = list(dict.fromkeys(payload.document_ids))
        documents = await self.documents.list_by_ids_for_org(
            organization_id, document_ids
        )
        if len(documents) != len(document_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "document_not_found",
                    "message": "One or more accounting documents were not found.",
                },
            )
        for document in documents:
            if document.status != AccountingDocumentStatus.APPROVED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "document_not_approved",
                        "message": "Only approved documents can be exported.",
                        "document_id": document.id,
                    },
                )

        batch = AccountingExportBatch(
            id=new_id("export"),
            organization_id=organization_id,
            status=AccountingExportBatchStatus.QUEUED.value,
            format=export_template.value,
            correlation_id=new_id("corr"),
            idempotency_key=idempotency_key,
            created_by_user_id=actor_user_id,
        )
        await self.batches.add(batch)
        self._ensure_export_batch_transition(
            batch.status, AccountingExportBatchStatus.COMPLETED.value
        )
        batch.status = AccountingExportBatchStatus.COMPLETED.value
        for document in documents:
            self._ensure_document_transition(
                document.status, AccountingDocumentStatus.EXPORTED.value
            )
            document.status = AccountingDocumentStatus.EXPORTED.value
            await self.items.add(
                AccountingExportItem(
                    id=new_id("exportitem"),
                    organization_id=organization_id,
                    batch_id=batch.id,
                    document_id=document.id,
                    status=AccountingDocumentStatus.EXPORTED.value,
                )
            )

        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=DomainEvent.EXPORT_BATCH_CREATED.value,
                resource_type="accounting_export_batch",
                resource_id=batch.id,
                correlation_id=batch.correlation_id,
                metadata={
                    "document_count": len(documents),
                    "format": export_template.value,
                },
            )
        )
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=DomainEvent.EXPORT_COMPLETED.value,
                resource_type="accounting_export_batch",
                resource_id=batch.id,
                correlation_id=batch.correlation_id,
                metadata={
                    "document_count": len(documents),
                    "format": export_template.value,
                },
            )
        )
        await self.session.commit()
        return {
            "id": batch.id,
            "status": batch.status,
            "format": batch.format,
            "document_count": len(documents),
        }

    async def download_export_batch(
        self, *, organization_id: str, actor_user_id: str, batch_id: str
    ) -> ExportArtifact:
        batch = await self.batches.get_for_org(organization_id, batch_id)
        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "export_batch_not_found",
                    "message": "Export batch was not found.",
                },
            )
        items = await self.items.list_for_batch(organization_id, batch_id)
        documents = await self.documents.list_by_ids_for_org(
            organization_id, [item.document_id for item in items]
        )
        if len(documents) != len(items):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "export_batch_incomplete",
                    "message": "Export batch references unavailable documents.",
                },
            )

        if batch.status == AccountingExportBatchStatus.COMPLETED.value:
            self._ensure_export_batch_transition(
                batch.status, AccountingExportBatchStatus.DOWNLOADED.value
            )
            batch.status = AccountingExportBatchStatus.DOWNLOADED.value
        elif batch.status != AccountingExportBatchStatus.DOWNLOADED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "export_batch_not_ready",
                    "message": "Export batch is not ready for download.",
                },
            )

        artifact = build_export_artifact(
            normalize_export_template(batch.format), documents
        )
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=DomainEvent.EXPORT_DOWNLOADED.value,
                resource_type="accounting_export_batch",
                resource_id=batch.id,
                correlation_id=batch.correlation_id,
                metadata={
                    "document_count": len(documents),
                    "format": batch.format,
                },
            )
        )
        await self.session.commit()
        return artifact

    def _ensure_document_transition(self, current_status: str, next_status: str) -> None:
        if can_document_transition(current_status, next_status):
            return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_document_transition",
                "message": "Document cannot move to the requested status.",
                "current_status": current_status,
                "next_status": next_status,
            },
        )

    def _ensure_export_batch_transition(
        self, current_status: str, next_status: str
    ) -> None:
        if can_export_batch_transition(current_status, next_status):
            return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_export_batch_transition",
                "message": "Export batch cannot move to the requested status.",
                "current_status": current_status,
                "next_status": next_status,
            },
        )


def build_export_idempotency_key(
    *, document_ids: list[str], export_format: str, requested_key: str | None
) -> str:
    source = requested_key or f"{export_format}:{','.join(sorted(set(document_ids)))}"
    return sha256(source.encode("utf-8")).hexdigest()
