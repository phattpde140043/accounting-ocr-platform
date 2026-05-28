import pytest
from fastapi import HTTPException

from app.domains.shared.file_service import FileService, FileUploadCreate, compute_content_hash


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def put_bytes(self, storage_key: str, content: bytes) -> None:
        self.objects[storage_key] = content

    async def get_bytes(self, storage_key: str) -> bytes:
        return self.objects[storage_key]

    async def delete(self, storage_key: str) -> None:
        self.objects.pop(storage_key, None)


class FakeFileAssetRepository:
    def __init__(self, existing=None) -> None:
        self.existing = existing
        self.added = None

    async def get_by_content_hash(self, organization_id: str, content_hash: str):
        return self.existing

    async def add(self, record):
        self.added = record
        return record


def test_compute_content_hash_is_deterministic_sha256() -> None:
    assert compute_content_hash(b"invoice") == compute_content_hash(b"invoice")
    assert len(compute_content_hash(b"invoice")) == 64


@pytest.mark.asyncio
async def test_file_service_stores_content_hash() -> None:
    service = FileService(session=None, storage=FakeStorage())  # type: ignore[arg-type]
    repository = FakeFileAssetRepository()
    service.repository = repository  # type: ignore[assignment]

    asset = await service.create_file_asset(
        FileUploadCreate(
            organization_id="org_1",
            created_by_user_id="user_1",
            original_name="invoice.pdf",
            mime_type="application/pdf",
            content=b"%PDF-1.7",
        )
    )

    assert asset.content_hash == compute_content_hash(b"%PDF-1.7")
    assert repository.added is asset


@pytest.mark.asyncio
async def test_file_service_rejects_duplicate_content_hash() -> None:
    existing = type("ExistingAsset", (), {"id": "file_existing"})()
    service = FileService(session=None, storage=FakeStorage())  # type: ignore[arg-type]
    service.repository = FakeFileAssetRepository(existing=existing)  # type: ignore[assignment]

    with pytest.raises(HTTPException) as exc_info:
        await service.create_file_asset(
            FileUploadCreate(
                organization_id="org_1",
                created_by_user_id="user_1",
                original_name="invoice.pdf",
                mime_type="application/pdf",
                content=b"%PDF-1.7",
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "duplicate_file"
