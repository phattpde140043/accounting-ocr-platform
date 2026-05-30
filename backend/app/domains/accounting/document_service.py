from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.model_mixins import new_id
from app.core.storage import StorageProvider
from app.domains.accounting.lifecycle import (
    AccountingDocumentStatus,
    can_document_transition,
)
from app.domains.accounting.metadata_policy import validate_document_metadata
from app.domains.accounting.models import AccountingDocument
from app.domains.accounting.repositories import (
    AccountingClientCompanyRepository,
    AccountingDocumentRepository,
)
from app.domains.accounting.schemas import CreateAccountingDocumentIn
from app.domains.platform.audit_service import AuditEventCreate, AuditLogService
from app.domains.platform.audit_catalog import DomainEvent
from app.domains.shared.file_service import FileService, FileUploadCreate


class AccountingDocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AccountingDocumentRepository(session)
        self.client_companies = AccountingClientCompanyRepository(session)
        self.audit_log = AuditLogService(session)

    async def list_documents(
        self,
        organization_id: str,
        *,
        status: str | None = None,
        client_company_id: str | None = None,
        accounting_period: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        documents = await self.repository.list_for_org(
            organization_id,
            status=status,
            client_company_id=client_company_id,
            accounting_period=accounting_period,
            limit=limit,
            offset=offset,
        )
        return [self._serialize(document) for document in documents]

    async def create_metadata_document(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        payload: CreateAccountingDocumentIn,
    ) -> dict:
        await self._ensure_valid_metadata(
            organization_id=organization_id,
            client_company_id=payload.client_company_id,
            document_type=payload.document_type,
            category=payload.category,
            accounting_period=payload.accounting_period,
        )
        document = AccountingDocument(
            id=new_id("doc"),
            organization_id=organization_id,
            client_company_id=payload.client_company_id,
            document_type=payload.document_type,
            category=payload.category,
            accounting_period=payload.accounting_period,
            file_asset_id=payload.file_asset_id,
            file_content_hash=payload.file_content_hash,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            status="uploaded",
            ocr_status="not_started",
            created_by_user_id=actor_user_id,
        )
        await self.repository.add(document)
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=DomainEvent.DOCUMENT_UPLOADED.value,
                resource_type="accounting_document",
                resource_id=document.id,
                metadata={"file_name": payload.file_name},
            )
        )
        await self.session.commit()
        return self._serialize(document)

    async def transition_document(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        document_id: str,
        next_status: str,
    ) -> dict:
        document = await self.repository.get_for_org(organization_id, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "document_not_found",
                    "message": "Accounting document was not found.",
                },
            )

        if not can_document_transition(document.status, next_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_document_transition",
                    "message": "Document cannot move to the requested status.",
                    "current_status": document.status,
                    "next_status": next_status,
                },
            )

        previous_status = document.status
        document.status = next_status
        if next_status == AccountingDocumentStatus.QUEUED.value:
            document.ocr_status = "queued"
        if next_status == AccountingDocumentStatus.PROCESSING.value:
            document.ocr_status = "processing"
        if next_status == AccountingDocumentStatus.NEEDS_REVIEW.value:
            document.ocr_status = "completed"

        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action="accounting.document_status_changed",
                resource_type="accounting_document",
                resource_id=document.id,
                metadata={
                    "previous_status": previous_status,
                    "next_status": next_status,
                },
            )
        )
        await self.session.commit()
        return self._serialize(document)

    async def upload_document(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        client_company_id: str,
        document_type: str,
        category: str,
        accounting_period: str,
        file_name: str,
        mime_type: str,
        content: bytes,
        storage: StorageProvider,
    ) -> dict:
        await self._ensure_valid_metadata(
            organization_id=organization_id,
            client_company_id=client_company_id,
            document_type=document_type,
            category=category,
            accounting_period=accounting_period,
        )
        file_service = FileService(self.session, storage)
        asset = await file_service.create_file_asset(
            FileUploadCreate(
                organization_id=organization_id,
                created_by_user_id=actor_user_id,
                original_name=file_name,
                mime_type=mime_type,
                content=content,
            )
        )
        try:
            return await self.create_metadata_document(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                payload=CreateAccountingDocumentIn(
                    client_company_id=client_company_id,
                    document_type=document_type,
                    category=category,
                    accounting_period=accounting_period,
                    file_asset_id=asset.id,
                    file_content_hash=asset.content_hash,
                    file_name=file_name,
                    mime_type=mime_type,
                ),
            )
        except Exception:
            await self.session.rollback()
            await storage.delete(asset.storage_key)
            raise

    async def _ensure_valid_metadata(
        self,
        *,
        organization_id: str,
        client_company_id: str,
        document_type: str,
        category: str,
        accounting_period: str,
    ) -> None:
        validate_document_metadata(
            document_type=document_type,
            category=category,
            accounting_period=accounting_period,
        )
        client_company = await self.client_companies.get_for_org(
            organization_id, client_company_id
        )
        if client_company is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "client_company_not_found",
                    "message": "Client company was not found for this organization.",
                },
            )

    def _serialize(self, document: AccountingDocument) -> dict:
        return {
            "id": document.id,
            "organization_id": document.organization_id,
            "client_company_id": document.client_company_id,
            "document_type": document.document_type,
            "category": document.category,
            "accounting_period": document.accounting_period,
            "file_name": document.file_name,
            "file_content_hash": document.file_content_hash,
            "mime_type": document.mime_type,
            "seller_tax_code": document.seller_tax_code,
            "invoice_number": document.invoice_number,
            "invoice_symbol": document.invoice_symbol,
            "invoice_date": document.invoice_date,
            "total_amount": document.total_amount,
            "status": document.status,
            "ocr_status": document.ocr_status,
            "created_at": document.created_at.isoformat() if document.created_at else "",
        }
