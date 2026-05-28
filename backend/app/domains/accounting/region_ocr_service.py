from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounting.repositories import AccountingDocumentRepository
from app.domains.accounting.schemas import RegionOcrIn
from app.domains.platform.audit_service import AuditEventCreate, AuditLogService


class RegionOcrService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.documents = AccountingDocumentRepository(session)
        self.audit_log = AuditLogService(session)

    async def process_regions(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        document_id: str,
        payload: RegionOcrIn,
    ) -> dict:
        document = await self.documents.get_for_org(organization_id, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "document_not_found",
                    "message": "Accounting document was not found.",
                },
            )

        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action="accounting.region_ocr_requested",
                resource_type="accounting_document",
                resource_id=document.id,
                metadata={"region_count": len(payload.regions)},
            )
        )
        await self.session.commit()
        return {
            "document_id": document.id,
            "regions": [
                {
                    "page": region.page,
                    "text": f"Mock OCR text for region {index + 1}",
                    "confidence": 0.88,
                    "box": region,
                }
                for index, region in enumerate(payload.regions)
            ],
        }

