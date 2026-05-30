from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_mixins import new_id
from app.domains.platform.models import AuditEvent
from app.domains.platform.repositories import AuditEventRepository

FORBIDDEN_METADATA_KEY_PARTS = (
    "access_token",
    "authorization",
    "content",
    "error_message",
    "password",
    "previous_value",
    "raw_payload",
    "refresh_token",
    "row",
    "secret",
    "token",
)


def validate_audit_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    for key, value in metadata.items():
        normalized_key = key.lower()
        if any(part in normalized_key for part in FORBIDDEN_METADATA_KEY_PARTS):
            raise ValueError(f"Audit metadata key is not allowed: {key}")
        if isinstance(value, dict):
            validate_audit_metadata(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    validate_audit_metadata(item)
    return metadata


@dataclass(frozen=True)
class AuditEventCreate:
    organization_id: str
    actor_user_id: str | None
    action: str
    resource_type: str
    resource_id: str
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = AuditEventRepository(session)

    async def record(self, payload: AuditEventCreate) -> AuditEvent:
        event = AuditEvent(
            id=new_id("audit"),
            organization_id=payload.organization_id,
            actor_user_id=payload.actor_user_id,
            action=payload.action,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            correlation_id=payload.correlation_id,
            metadata_json=validate_audit_metadata(payload.metadata),
            ip_address=payload.ip_address,
            user_agent=payload.user_agent,
        )
        return await self.repository.add(event)
