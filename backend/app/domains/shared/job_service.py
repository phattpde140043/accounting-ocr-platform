from enum import StrEnum
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_mixins import new_id
from app.domains.platform.audit_service import AuditEventCreate, AuditLogService
from app.domains.shared.models import BackgroundJob
from app.domains.shared.repositories import BackgroundJobRepository


class BackgroundJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BackgroundJobType(StrEnum):
    ACCOUNTING_OCR = "accounting_ocr"


class BackgroundJobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = BackgroundJobRepository(session)
        self.audit_log = AuditLogService(session)

    async def create_job(
        self,
        *,
        organization_id: str,
        actor_user_id: str | None,
        job_type: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        correlation_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BackgroundJob:
        correlation_id = correlation_id or new_id("corr")
        job = BackgroundJob(
            id=new_id("job"),
            organization_id=organization_id,
            job_type=job_type,
            status=BackgroundJobStatus.QUEUED.value,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            attempts=0,
            max_attempts=4,
            available_at=datetime.now(timezone.utc),
            payload=payload or {},
        )
        await self.repository.add(job)
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action="background_job.created",
                resource_type="background_job",
                resource_id=job.id,
                correlation_id=correlation_id,
                metadata={
                    "job_type": job_type,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                },
            )
        )
        await self.session.commit()
        return job

    async def get_for_resource(
        self, organization_id: str, resource_type: str, resource_id: str
    ) -> BackgroundJob | None:
        return await self.repository.get_for_resource(
            organization_id, resource_type, resource_id
        )

    async def mark_processing(self, organization_id: str, job_id: str) -> BackgroundJob:
        job = await self._get_job(organization_id, job_id)
        job.status = BackgroundJobStatus.PROCESSING.value
        job.attempts += 1
        await self.session.commit()
        return job

    async def claim_next(self, *, worker_id: str) -> BackgroundJob | None:
        job = await self.repository.claim_next(worker_id=worker_id)
        await self.session.commit()
        return job

    async def mark_completed(
        self, *, organization_id: str, actor_user_id: str | None, job_id: str
    ) -> BackgroundJob:
        job = await self._get_job(organization_id, job_id)
        job.status = BackgroundJobStatus.COMPLETED.value
        job.locked_by = None
        job.locked_until = None
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action="background_job.completed",
                resource_type="background_job",
                resource_id=job.id,
                correlation_id=job.correlation_id,
            )
        )
        await self.session.commit()
        return job

    async def mark_failed(
        self,
        *,
        organization_id: str,
        actor_user_id: str | None,
        job_id: str,
        error_message: str,
        retryable: bool = True,
    ) -> BackgroundJob:
        job = await self._get_job(organization_id, job_id)
        should_retry = retryable and job.attempts < job.max_attempts
        job.status = (
            BackgroundJobStatus.QUEUED.value
            if should_retry
            else BackgroundJobStatus.FAILED.value
        )
        job.available_at = (
            datetime.now(timezone.utc) + retry_delay_for_attempt(job.attempts)
            if should_retry
            else None
        )
        job.locked_by = None
        job.locked_until = None
        job.error_message = error_message
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=(
                    "background_job.retry_scheduled"
                    if should_retry
                    else "background_job.failed"
                ),
                resource_type="background_job",
                resource_id=job.id,
                correlation_id=job.correlation_id,
                metadata={
                    "error_type": error_message,
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                },
            )
        )
        await self.session.commit()
        return job

    async def _get_job(self, organization_id: str, job_id: str) -> BackgroundJob:
        job = await self.repository.get_for_org(organization_id, job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "background_job_not_found",
                    "message": "Background job was not found.",
                },
            )
        return job


def retry_delay_for_attempt(attempts: int) -> timedelta:
    retry_seconds = (0, 60, 300, 1800)
    index = min(max(attempts - 1, 0), len(retry_seconds) - 1)
    return timedelta(seconds=retry_seconds[index])
