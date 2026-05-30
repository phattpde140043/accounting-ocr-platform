import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_mixins import new_id
from app.domains.accounting.ocr_provider import UnknownOcrProviderError
from app.domains.accounting.ocr_service import AccountingOcrService
from app.domains.shared.job_service import BackgroundJobService, BackgroundJobType


class BackgroundWorker:
    def __init__(
        self,
        session: AsyncSession,
        poll_interval_seconds: float = 2.0,
        worker_id: str | None = None,
    ) -> None:
        self.session = session
        self.job_service = BackgroundJobService(session)
        self.poll_interval_seconds = poll_interval_seconds
        self.worker_id = worker_id or new_id("worker")

    async def run_once(self) -> bool:
        job = await self.job_service.claim_next(worker_id=self.worker_id)
        if job is None:
            return False

        try:
            if job.job_type == BackgroundJobType.ACCOUNTING_OCR.value:
                await AccountingOcrService(self.session).execute_ocr_job(
                    organization_id=job.organization_id,
                    actor_user_id=None,
                    ocr_job_id=job.resource_id or "",
                )
            else:
                raise ValueError(f"Unsupported job type: {job.job_type}")

            await self.job_service.mark_completed(
                organization_id=job.organization_id,
                actor_user_id=None,
                job_id=job.id,
            )
        except Exception as exc:
            await self.job_service.mark_failed(
                organization_id=job.organization_id,
                actor_user_id=None,
                job_id=job.id,
                error_message=type(exc).__name__,
                retryable=not isinstance(exc, UnknownOcrProviderError),
            )
        return True

    async def run_forever(self) -> None:
        while True:
            processed = await self.run_once()
            if not processed:
                await asyncio.sleep(self.poll_interval_seconds)
