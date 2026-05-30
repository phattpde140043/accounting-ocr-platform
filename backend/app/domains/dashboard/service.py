from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounting.models import (
    AccountingDocument,
    AccountingExportBatch,
    AccountingOcrJob,
)
from app.domains.platform.models import AuditEvent
from app.domains.shared.job_service import BackgroundJobType
from app.domains.shared.models import BackgroundJob


class DashboardAggregationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self, *, organization_id: str, role: str) -> dict:
        metrics = await self._get_operational_metrics(organization_id)
        cards = [
            {"label": "Documents", "value": metrics["documents"]},
            {"label": "OCR Queue", "value": metrics["ocr_queue"]},
            {"label": "OCR Failures", "value": metrics["ocr_failures"]},
            {"label": "Needs Review", "value": metrics["needs_review"]},
            {"label": "Review SLA Breaches", "value": metrics["review_sla_breaches"]},
            {"label": "Export Batches", "value": metrics["export_batches"]},
            {"label": "Audit Events", "value": metrics["audit_events"]},
        ]
        if role != "admin":
            cards = [card for card in cards if card["label"] != "Audit Events"]
        return {
            "role": role,
            "cards": cards,
        }

    async def get_role_dashboard(
        self, *, organization_id: str, role: str, focus: str
    ) -> dict:
        summary = await self.get_summary(organization_id=organization_id, role=role)
        summary["focus"] = focus
        return summary

    async def _get_operational_metrics(self, organization_id: str) -> dict[str, int]:
        review_sla_cutoff = datetime.now(UTC) - timedelta(hours=4)
        statement = select(
            self._count(AccountingDocument, organization_id).label("documents"),
            self._count(
                BackgroundJob,
                organization_id,
                BackgroundJob.job_type == BackgroundJobType.ACCOUNTING_OCR.value,
                BackgroundJob.status.in_(("queued", "processing")),
            ).label("ocr_queue"),
            self._count(
                AccountingOcrJob,
                organization_id,
                AccountingOcrJob.status == "failed",
            ).label("ocr_failures"),
            self._count(
                AccountingDocument,
                organization_id,
                AccountingDocument.status == "needs_review",
            ).label("needs_review"),
            self._count(
                AccountingDocument,
                organization_id,
                AccountingDocument.status == "needs_review",
                AccountingDocument.created_at < review_sla_cutoff,
            ).label("review_sla_breaches"),
            self._count(AccountingExportBatch, organization_id).label("export_batches"),
            self._count(AuditEvent, organization_id).label("audit_events"),
        )
        row = (await self.session.execute(statement)).mappings().one()
        return {key: int(value or 0) for key, value in row.items()}

    @staticmethod
    def _count(model: type, organization_id: str, *conditions):
        return (
            select(func.count())
            .select_from(model)
            .where(model.organization_id == organization_id, *conditions)
            .scalar_subquery()
        )
