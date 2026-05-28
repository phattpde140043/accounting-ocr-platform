from pathlib import Path
import re
from typing import Protocol

from fastapi import HTTPException, status

from app.core.config import settings


ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

ALLOWED_EXTENSIONS_BY_MIME_TYPE = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
}

SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class StorageProvider(Protocol):
    async def put_bytes(self, storage_key: str, content: bytes) -> None:
        """Store bytes by storage key."""

    async def get_bytes(self, storage_key: str) -> bytes:
        """Read bytes by storage key."""

    async def delete(self, storage_key: str) -> None:
        """Delete a stored object."""


class LocalStorageProvider:
    def __init__(self, root: str = settings.local_storage_root) -> None:
        self.root = Path(root)

    async def put_bytes(self, storage_key: str, content: bytes) -> None:
        path = self._resolve(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    async def get_bytes(self, storage_key: str) -> bytes:
        return self._resolve(storage_key).read_bytes()

    async def delete(self, storage_key: str) -> None:
        path = self._resolve(storage_key)
        if path.exists():
            path.unlink()

    def _resolve(self, storage_key: str) -> Path:
        path = (self.root / storage_key).resolve()
        root = self.root.resolve()
        if root not in path.parents and path != root:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_storage_key",
                    "message": "Storage key resolves outside the configured storage root.",
                },
            )
        return path


def validate_upload(
    *,
    mime_type: str,
    size_bytes: int,
    file_name: str | None = None,
    content: bytes | None = None,
) -> None:
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "unsupported_file_type",
                "message": "Only PDF, JPG and PNG files are supported.",
            },
        )
    if size_bytes > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "file_too_large",
                "message": "Uploaded file exceeds the configured size limit.",
            },
        )
    if file_name is not None:
        extension = Path(file_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS_BY_MIME_TYPE[mime_type]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "file_extension_mismatch",
                    "message": "File extension does not match the declared MIME type.",
                },
            )
    if content is not None and not _matches_file_signature(mime_type, content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "file_signature_mismatch",
                "message": "File content does not match the declared MIME type.",
            },
        )


def sanitize_filename(file_name: str) -> str:
    base_name = Path(file_name).name.strip() or "upload.bin"
    sanitized = SAFE_FILENAME_PATTERN.sub("_", base_name)
    sanitized = sanitized.strip("._")
    return sanitized or "upload.bin"


def _matches_file_signature(mime_type: str, content: bytes) -> bool:
    if mime_type == "application/pdf":
        return content.startswith(b"%PDF")
    if mime_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if mime_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    return False
