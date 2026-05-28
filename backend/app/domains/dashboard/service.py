from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounting.models import AccountingDocument
from app.domains.platform.models import AuditEvent


class DashboardAggregationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self, *, organization_id: str, role: str) -> dict:
        documents = await self._count(AccountingDocument, organization_id)
        audit_events = await self._count(AuditEvent, organization_id)
        return {
            "role": role,
            "cards": [
                {"label": "Documents", "value": documents},
                {"label": "OCR Queue", "value": 0},
                {"label": "Needs Review", "value": 0},
                {"label": "Export Batches", "value": 0},
                {"label": "Audit Events", "value": audit_events},
            ],
            "next_build_steps": [
                "Add OCR throughput charts",
                "Add reviewer productivity metrics",
                "Add export SLA metrics",
            ],
        }

    async def get_role_dashboard(
        self, *, organization_id: str, role: str, focus: str
    ) -> dict:
        summary = await self.get_summary(organization_id=organization_id, role=role)
        summary["focus"] = focus
        return summary

    async def _count(self, model: type, organization_id: str) -> int:
        value = await self.session.scalar(
            select(func.count()).select_from(model).where(
                model.organization_id == organization_id
            )
        )
        return int(value or 0)
