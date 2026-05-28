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
from app.domains.accounting.export_templates import normalize_export_template
from app.domains.platform.audit_service import AuditEventCreate, AuditLogService


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
        documents = []
        for document_id in payload.document_ids:
            document = await self.documents.get_for_org(organization_id, document_id)
            if document is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "document_not_found",
                        "message": "Accounting document was not found.",
                    },
                )
            if document.status != AccountingDocumentStatus.APPROVED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "document_not_approved",
                        "message": "Only approved documents can be exported.",
                        "document_id": document.id,
                    },
                )
            documents.append(document)

        batch = AccountingExportBatch(
            id=new_id("export"),
            organization_id=organization_id,
            status=AccountingExportBatchStatus.QUEUED.value,
            format=export_template.value,
            correlation_id=new_id("corr"),
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
                action="accounting.export_batch_created",
                resource_type="accounting_export_batch",
                resource_id=batch.id,
                correlation_id=batch.correlation_id,
                metadata={
                    "document_ids": payload.document_ids,
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

    async def download_export_batch(self, organization_id: str, batch_id: str) -> dict:
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
        documents = []
        for item in items:
            document = await self.documents.get_for_org(organization_id, item.document_id)
            if document is not None:
                documents.append(
                    {
                        "id": document.id,
                        "client_company_id": document.client_company_id,
                        "document_type": document.document_type,
                        "category": document.category,
                        "accounting_period": document.accounting_period,
                        "file_name": document.file_name,
                        "status": document.status,
                    }
                )
        return {
            "batch_id": batch.id,
            "format": batch.format,
            "documents": documents,
        }

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
