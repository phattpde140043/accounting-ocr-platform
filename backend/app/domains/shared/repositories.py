from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.domains.shared.models import BackgroundJob, FileAsset


class FileAssetRepository(BaseRepository[FileAsset]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FileAsset)

    async def get_by_content_hash(
        self, organization_id: str, content_hash: str
    ) -> FileAsset | None:
        return await self.session.scalar(
            select(FileAsset).where(
                FileAsset.organization_id == organization_id,
                FileAsset.content_hash == content_hash,
            )
        )


class BackgroundJobRepository(BaseRepository[BackgroundJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BackgroundJob)

    async def get_for_resource(
        self, organization_id: str, resource_type: str, resource_id: str
    ) -> BackgroundJob | None:
        return await self.session.scalar(
            select(BackgroundJob)
            .where(
                BackgroundJob.organization_id == organization_id,
                BackgroundJob.resource_type == resource_type,
                BackgroundJob.resource_id == resource_id,
            )
            .order_by(BackgroundJob.created_at.desc())
            .limit(1)
        )

    async def get_next_queued(self) -> BackgroundJob | None:
        return await self.session.scalar(
            select(BackgroundJob)
            .where(BackgroundJob.status == "queued")
            .order_by(BackgroundJob.created_at.asc())
            .limit(1)
        )

    async def claim_next(
        self, *, worker_id: str, lock_seconds: int = 300
    ) -> BackgroundJob | None:
        now = datetime.now(timezone.utc)
        claimable = or_(
            and_(
                BackgroundJob.status == "queued",
                or_(
                    BackgroundJob.available_at.is_(None),
                    BackgroundJob.available_at <= now,
                ),
            ),
            and_(
                BackgroundJob.status == "processing",
                BackgroundJob.locked_until < now,
            ),
        )
        job = await self.session.scalar(
            select(BackgroundJob)
            .where(
                claimable,
                BackgroundJob.attempts < BackgroundJob.max_attempts,
            )
            .order_by(BackgroundJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None

        job.status = "processing"
        job.locked_by = worker_id
        job.locked_until = now + timedelta(seconds=lock_seconds)
        job.attempts += 1
        await self.session.flush()
        return job
