from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_mixins import new_id
from app.domains.accounting.confidence_policy import (
    REQUIRED_FIELDS,
    classify_confidence,
    confidence_level,
)
from app.domains.accounting.lifecycle import (
    AccountingDocumentStatus,
    AccountingOcrJobStatus,
    AccountingOcrResultStatus,
    can_document_transition,
    can_ocr_job_transition,
    can_ocr_result_transition,
)
from app.domains.accounting.models import AccountingOcrField, AccountingOcrJob, AccountingOcrResult
from app.domains.accounting.metadata_policy import INVOICE_IDENTITY_FIELDS
from app.domains.accounting.ocr_provider import (
    OcrDocumentContext,
    get_ocr_provider,
)
from app.domains.accounting.repositories import (
    AccountingDocumentRepository,
    AccountingOcrFieldRepository,
    AccountingOcrJobRepository,
    AccountingOcrResultRepository,
)
from app.domains.platform.audit_service import AuditEventCreate, AuditLogService
from app.domains.platform.audit_catalog import DomainEvent
from app.domains.shared.job_service import BackgroundJobService, BackgroundJobType
from app.domains.shared.repositories import FileAssetRepository


class AccountingOcrService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.documents = AccountingDocumentRepository(session)
        self.ocr_jobs = AccountingOcrJobRepository(session)
        self.ocr_results = AccountingOcrResultRepository(session)
        self.ocr_fields = AccountingOcrFieldRepository(session)
        self.file_assets = FileAssetRepository(session)
        self.background_jobs = BackgroundJobService(session)
        self.audit_log = AuditLogService(session)

    async def request_ocr(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        document_id: str,
        provider: str = "mock",
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

        await self._ensure_file_ready_for_ocr(
            organization_id=organization_id,
            file_asset_id=document.file_asset_id,
        )
        existing_job = await self.ocr_jobs.get_active_for_document_provider(
            organization_id=organization_id,
            document_id=document_id,
            provider=provider,
        )
        if existing_job is not None:
            background_job = await self.background_jobs.get_for_resource(
                organization_id,
                "accounting_ocr_job",
                existing_job.id,
            )
            return {
                "status": existing_job.status,
                "ocr_job_id": existing_job.id,
                "background_job_id": background_job.id if background_job else "",
            }

        correlation_id = new_id("corr")
        ocr_job = AccountingOcrJob(
            id=new_id("ocrjob"),
            organization_id=organization_id,
            document_id=document_id,
            provider=provider,
            status=AccountingOcrJobStatus.QUEUED.value,
            correlation_id=correlation_id,
            attempts=0,
        )
        await self.ocr_jobs.add(ocr_job)
        background_job = await self.background_jobs.create_job(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            job_type=BackgroundJobType.ACCOUNTING_OCR.value,
            resource_type="accounting_ocr_job",
            resource_id=ocr_job.id,
            correlation_id=correlation_id,
            payload={"document_id": document_id, "provider": provider},
        )
        self._ensure_document_transition(
            document.status, AccountingDocumentStatus.QUEUED.value
        )
        document.status = AccountingDocumentStatus.QUEUED.value
        document.ocr_status = AccountingOcrJobStatus.QUEUED.value
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=DomainEvent.DOCUMENT_QUEUED_FOR_OCR.value,
                resource_type="accounting_document",
                resource_id=document_id,
                correlation_id=correlation_id,
                metadata={
                    "ocr_job_id": ocr_job.id,
                    "background_job_id": background_job.id,
                    "provider": provider,
                    "correlation_id": correlation_id,
                },
            )
        )
        await self.session.commit()
        return {
            "status": "queued",
            "ocr_job_id": ocr_job.id,
            "background_job_id": background_job.id,
        }

    async def _ensure_file_ready_for_ocr(
        self, *, organization_id: str, file_asset_id: str | None
    ) -> None:
        asset = (
            await self.file_assets.get_for_org(organization_id, file_asset_id)
            if file_asset_id
            else None
        )
        if asset is None or asset.status != "stored":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "file_not_ready_for_ocr",
                    "message": "Document file must pass upload security checks before OCR.",
                },
            )

    async def execute_ocr_job(
        self,
        *,
        organization_id: str,
        actor_user_id: str | None,
        ocr_job_id: str,
    ) -> dict:
        ocr_job = await self.ocr_jobs.get_for_org(organization_id, ocr_job_id)
        if ocr_job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ocr_job_not_found",
                    "message": "OCR job was not found.",
                },
            )

        document = await self.documents.get_for_org(organization_id, ocr_job.document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "document_not_found",
                    "message": "Accounting document was not found.",
                },
            )

        if ocr_job.status == AccountingOcrJobStatus.FAILED.value:
            self._ensure_ocr_job_transition(
                ocr_job.status, AccountingOcrJobStatus.QUEUED.value
            )
            self._ensure_document_transition(
                document.status, AccountingDocumentStatus.QUEUED.value
            )
            ocr_job.status = AccountingOcrJobStatus.QUEUED.value
            document.status = AccountingDocumentStatus.QUEUED.value

        self._ensure_ocr_job_transition(
            ocr_job.status, AccountingOcrJobStatus.PROCESSING.value
        )
        self._ensure_document_transition(
            document.status, AccountingDocumentStatus.PROCESSING.value
        )
        ocr_job.status = AccountingOcrJobStatus.PROCESSING.value
        ocr_job.attempts += 1
        document.status = AccountingDocumentStatus.PROCESSING.value
        document.ocr_status = AccountingOcrJobStatus.PROCESSING.value
        await self.session.flush()

        try:
            provider = get_ocr_provider(ocr_job.provider)
            provider_result = await provider.extract(
                OcrDocumentContext(
                    document_id=document.id,
                    file_name=document.file_name,
                    mime_type=document.mime_type,
                    file_asset_id=document.file_asset_id,
                )
            )
            confidence_decision = classify_confidence(
                confidence=provider_result.confidence,
                extracted_fields={
                    field.key: field.value for field in provider_result.fields
                },
            )
            result = AccountingOcrResult(
                id=new_id("ocrresult"),
                organization_id=organization_id,
                document_id=document.id,
                job_id=ocr_job.id,
                status=AccountingOcrResultStatus.NEEDS_REVIEW.value,
                confidence=provider_result.confidence,
                review_route=confidence_decision.route.value,
                review_reasons=list(confidence_decision.reasons),
                raw_payload=provider_result.raw_payload,
            )
            await self.ocr_results.add(result)
            for field in provider_result.fields:
                await self.ocr_fields.add(
                    AccountingOcrField(
                        id=new_id("ocrfield"),
                        organization_id=organization_id,
                        result_id=result.id,
                        field_key=field.key,
                        field_value=field.value,
                        confidence=field.confidence,
                        source="ocr",
                        version=1,
                    )
                )

            self._ensure_ocr_job_transition(
                ocr_job.status, AccountingOcrJobStatus.COMPLETED.value
            )
            self._ensure_document_transition(
                document.status, AccountingDocumentStatus.NEEDS_REVIEW.value
            )
            ocr_job.status = AccountingOcrJobStatus.COMPLETED.value
            document.status = AccountingDocumentStatus.NEEDS_REVIEW.value
            document.ocr_status = AccountingOcrJobStatus.COMPLETED.value
            await self.audit_log.record(
                AuditEventCreate(
                    organization_id=organization_id,
                    actor_user_id=actor_user_id,
                    action=DomainEvent.OCR_COMPLETED.value,
                    resource_type="accounting_document",
                    resource_id=document.id,
                    correlation_id=ocr_job.correlation_id,
                    metadata={"ocr_job_id": ocr_job.id, "ocr_result_id": result.id},
                )
            )
            await self.session.commit()
            return {
                "status": "completed",
                "ocr_job_id": ocr_job.id,
                "ocr_result_id": result.id,
                "review_route": confidence_decision.route.value,
            }
        except Exception as exc:
            self._ensure_ocr_job_transition(
                ocr_job.status, AccountingOcrJobStatus.FAILED.value
            )
            self._ensure_document_transition(
                document.status, AccountingDocumentStatus.FAILED.value
            )
            ocr_job.status = AccountingOcrJobStatus.FAILED.value
            ocr_job.error_message = type(exc).__name__
            document.status = AccountingDocumentStatus.FAILED.value
            document.ocr_status = AccountingOcrJobStatus.FAILED.value
            await self.audit_log.record(
                AuditEventCreate(
                    organization_id=organization_id,
                    actor_user_id=actor_user_id,
                    action=DomainEvent.OCR_FAILED.value,
                    resource_type="accounting_document",
                    resource_id=document.id,
                    correlation_id=ocr_job.correlation_id,
                    metadata={
                        "ocr_job_id": ocr_job.id,
                        "error_type": type(exc).__name__,
                    },
                )
            )
            await self.session.commit()
            raise

    async def get_result_for_document(
        self, *, organization_id: str, document_id: str
    ) -> dict:
        result = await self.ocr_results.get_latest_for_document(
            organization_id, document_id
        )
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ocr_result_not_found",
                    "message": "OCR result was not found.",
                },
            )
        fields = await self.ocr_fields.list_for_result(organization_id, result.id)
        return {
            "result_id": result.id,
            "document_id": result.document_id,
            "status": result.status,
            "confidence": float(result.confidence or 0),
            "confidence_level": confidence_level(float(result.confidence or 0)).value,
            "review_route": result.review_route,
            "review_reasons": result.review_reasons,
            "fields": {field.field_key: field.field_value for field in fields},
            "field_items": [
                {
                    "id": field.id,
                    "key": field.field_key,
                    "value": field.field_value,
                    "confidence": float(field.confidence or 0),
                    "source": field.source,
                    "version": field.version,
                }
                for field in fields
            ],
        }

    async def update_field(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        result_id: str,
        field_id: str,
        value: str,
        version: int,
    ) -> dict:
        field = await self.ocr_fields.get_for_org(organization_id, field_id)
        if field is None or field.result_id != result_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ocr_field_not_found",
                    "message": "OCR field was not found.",
                },
            )
        previous_value = field.field_value
        if field.version != version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "stale_ocr_field_version",
                    "message": "OCR field was changed by another reviewer.",
                    "current_version": field.version,
                },
            )
        field.field_value = value
        field.source = "manual"
        field.version += 1
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=DomainEvent.OCR_FIELD_CORRECTED.value,
                resource_type="accounting_ocr_field",
                resource_id=field.id,
                metadata={
                    "result_id": result_id,
                    "field_key": field.field_key,
                    "value_changed": previous_value != value,
                },
            )
        )
        await self.session.commit()
        return {
            "id": field.id,
            "result_id": field.result_id,
            "field_key": field.field_key,
            "field_value": field.field_value,
            "source": field.source,
            "version": field.version,
        }

    async def approve_result(
        self, *, organization_id: str, actor_user_id: str, result_id: str
    ) -> dict:
        result = await self.ocr_results.get_for_org(organization_id, result_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ocr_result_not_found",
                    "message": "OCR result was not found.",
                },
            )
        document = await self.documents.get_for_org(organization_id, result.document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "document_not_found",
                    "message": "Accounting document was not found.",
                },
            )
        self._ensure_ocr_result_transition(
            result.status, AccountingOcrResultStatus.APPROVED.value
        )
        self._ensure_document_transition(
            document.status, AccountingDocumentStatus.APPROVED.value
        )
        fields = await self.ocr_fields.list_for_result(organization_id, result.id)
        self._ensure_required_review_fields(fields)
        await self._promote_invoice_identity(
            organization_id=organization_id,
            document=document,
            fields=fields,
        )
        result.status = AccountingOcrResultStatus.APPROVED.value
        document.status = AccountingDocumentStatus.APPROVED.value
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=DomainEvent.OCR_RESULT_APPROVED.value,
                resource_type="accounting_ocr_result",
                resource_id=result.id,
                metadata={"document_id": document.id},
            )
        )
        await self.session.commit()
        return {
            "status": "approved",
            "document_id": document.id,
            "result_id": result.id,
            "confidence": float(result.confidence or 0),
            "confidence_level": confidence_level(float(result.confidence or 0)).value,
            "review_route": result.review_route,
            "review_reasons": result.review_reasons,
            "fields": {},
        }

    async def _promote_invoice_identity(
        self, *, organization_id: str, document, fields: list[AccountingOcrField]
    ) -> None:
        values = {
            field.field_key: field.field_value
            for field in fields
            if field.field_key in INVOICE_IDENTITY_FIELDS and field.field_value
        }
        if len(values) != len(INVOICE_IDENTITY_FIELDS):
            return

        existing = await self.documents.get_by_invoice_identity(
            organization_id=organization_id,
            seller_tax_code=values["seller_tax_code"],
            invoice_number=values["invoice_number"],
            invoice_symbol=values["invoice_symbol"],
            invoice_date=values["invoice_date"],
            total_amount=values["total_amount"],
            exclude_document_id=document.id,
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "duplicate_invoice_identity",
                    "message": "An approved document already uses this invoice identity.",
                },
            )

        for field_name, field_value in values.items():
            setattr(document, field_name, field_value)

    def _ensure_required_review_fields(self, fields: list[AccountingOcrField]) -> None:
        values = {field.field_key: field.field_value for field in fields}
        missing_fields = sorted(field for field in REQUIRED_FIELDS if not values.get(field))
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "required_ocr_fields_missing",
                    "message": "Required OCR fields must be reviewed before approval.",
                    "missing_fields": missing_fields,
                },
            )

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

    def _ensure_ocr_job_transition(self, current_status: str, next_status: str) -> None:
        if can_ocr_job_transition(current_status, next_status):
            return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_ocr_job_transition",
                "message": "OCR job cannot move to the requested status.",
                "current_status": current_status,
                "next_status": next_status,
            },
        )

    def _ensure_ocr_result_transition(
        self, current_status: str, next_status: str
    ) -> None:
        if can_ocr_result_transition(current_status, next_status):
            return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_ocr_result_transition",
                "message": "OCR result cannot move to the requested status.",
                "current_status": current_status,
                "next_status": next_status,
            },
        )
