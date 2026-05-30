from dataclasses import dataclass
from hashlib import sha256

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_mixins import new_id
from app.core.storage import StorageProvider, sanitize_filename, validate_upload
from app.domains.shared.file_scan import FileScanner, get_file_scanner
from app.domains.shared.models import FileAsset
from app.domains.shared.repositories import FileAssetRepository


@dataclass(frozen=True)
class FileUploadCreate:
    organization_id: str
    created_by_user_id: str
    original_name: str
    mime_type: str
    content: bytes


class FileService:
    def __init__(
        self,
        session: AsyncSession,
        storage: StorageProvider,
        scanner: FileScanner | None = None,
    ) -> None:
        self.repository = FileAssetRepository(session)
        self.storage = storage
        self.scanner = scanner or get_file_scanner()

    async def create_file_asset(self, payload: FileUploadCreate) -> FileAsset:
        size_bytes = len(payload.content)
        safe_name = sanitize_filename(payload.original_name)
        validate_upload(
            mime_type=payload.mime_type,
            size_bytes=size_bytes,
            file_name=safe_name,
            content=payload.content,
        )
        content_hash = compute_content_hash(payload.content)
        existing = await self.repository.get_by_content_hash(
            payload.organization_id, content_hash
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "duplicate_file",
                    "message": "A file with the same content already exists.",
                    "file_asset_id": existing.id,
                },
            )

        file_id = new_id("file")
        storage_key = f"{payload.organization_id}/{file_id}/{safe_name}"
        await self.storage.put_bytes(storage_key, payload.content)
        try:
            scan_result = await self.scanner.scan(
                content=payload.content, mime_type=payload.mime_type
            )
            asset = FileAsset(
                id=file_id,
                organization_id=payload.organization_id,
                original_name=safe_name,
                storage_key=storage_key,
                mime_type=payload.mime_type,
                size_bytes=size_bytes,
                content_hash=content_hash,
                status="stored" if scan_result.is_clean else "quarantined",
                created_by_user_id=payload.created_by_user_id,
            )
            return await self.repository.add(asset)
        except Exception:
            await self.storage.delete(storage_key)
            raise


def compute_content_hash(content: bytes) -> str:
    return sha256(content).hexdigest()
