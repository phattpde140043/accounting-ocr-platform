from datetime import timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.dialects import postgresql

from app.domains.shared.job_service import BackgroundJobService, retry_delay_for_attempt
from app.domains.shared.repositories import BackgroundJobRepository


class _ClaimSession:
    def __init__(self, job) -> None:
        self.job = job
        self.statement = None
        self.flushed = False

    async def scalar(self, statement):
        self.statement = statement
        return self.job

    async def flush(self) -> None:
        self.flushed = True


@pytest.mark.asyncio
async def test_claim_next_uses_skip_locked_and_assigns_lease() -> None:
    job = SimpleNamespace(
        status="queued",
        locked_by=None,
        locked_until=None,
        attempts=0,
    )
    session = _ClaimSession(job)
    repository = BackgroundJobRepository(session)  # type: ignore[arg-type]

    claimed = await repository.claim_next(worker_id="worker_1", lock_seconds=60)

    sql = str(
        session.statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert claimed is job
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert "background_jobs.attempts < background_jobs.max_attempts" in sql
    assert job.status == "processing"
    assert job.locked_by == "worker_1"
    assert job.attempts == 1
    assert session.flushed is True


def test_retry_schedule_uses_bounded_backoff() -> None:
    assert retry_delay_for_attempt(1) == timedelta(seconds=0)
    assert retry_delay_for_attempt(2) == timedelta(minutes=1)
    assert retry_delay_for_attempt(3) == timedelta(minutes=5)
    assert retry_delay_for_attempt(4) == timedelta(minutes=30)
    assert retry_delay_for_attempt(99) == timedelta(minutes=30)


@pytest.mark.asyncio
async def test_terminal_failure_clears_worker_lock() -> None:
    job = SimpleNamespace(
        id="job_1",
        status="processing",
        attempts=1,
        max_attempts=4,
        locked_by="worker_1",
        locked_until=object(),
        available_at=None,
        error_message=None,
        correlation_id="corr_1",
    )

    class _Repository:
        async def get_for_org(self, organization_id: str, job_id: str):
            return job

    class _AuditLog:
        async def record(self, payload) -> None:
            self.payload = payload

    class _Session:
        async def commit(self) -> None:
            return None

    service = BackgroundJobService(_Session())  # type: ignore[arg-type]
    service.repository = _Repository()  # type: ignore[assignment]
    service.audit_log = _AuditLog()  # type: ignore[assignment]

    result = await service.mark_failed(
        organization_id="org_1",
        actor_user_id=None,
        job_id="job_1",
        error_message="unknown provider",
        retryable=False,
    )

    assert result.status == "failed"
    assert result.locked_by is None
    assert result.locked_until is None
    assert result.available_at is None
