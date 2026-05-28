from sqlalchemy import select
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

    async def get_next_queued(self) -> BackgroundJob | None:
        return await self.session.scalar(
            select(BackgroundJob)
            .where(BackgroundJob.status == "queued")
            .order_by(BackgroundJob.created_at.asc())
            .limit(1)
        )
