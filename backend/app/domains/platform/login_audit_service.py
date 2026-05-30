import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_mixins import new_id
from app.domains.platform.models import LoginEvent

logger = logging.getLogger(__name__)


class LoginAuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_success(
        self,
        *,
        organization_id: str,
        user_id: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        self.session.add(
            LoginEvent(
                id=new_id("login"),
                organization_id=organization_id,
                user_id=user_id,
                provider="google",
                result="success",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        await self.session.commit()

    @staticmethod
    def record_rejection(*, reason: str) -> None:
        # Rejected callbacks may not have a trusted tenant or user identity yet.
        logger.warning("google_sso_rejected reason=%s", reason)
