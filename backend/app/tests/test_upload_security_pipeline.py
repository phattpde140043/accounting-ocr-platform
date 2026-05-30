import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.domains.accounting.document_service import AccountingDocumentService
from app.domains.accounting.ocr_service import AccountingOcrService
from app.domains.shared.file_service import FileService
from app.domains.shared.file_scan import LocalNoOpFileScanner, get_file_scanner


def test_local_environment_can_use_explicit_noop_scanner(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "local")
    monkeypatch.setattr(settings, "file_scanner_mode", "local-noop")

    assert isinstance(get_file_scanner(), LocalNoOpFileScanner)


def test_production_environment_fails_closed_without_real_scanner(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "file_scanner_mode", "local-noop")

    with pytest.raises(RuntimeError, match="production antivirus"):
        get_file_scanner()


class _FileAssetRepository:
    def __init__(self, asset) -> None:
        self.asset = asset

    async def get_for_org(self, organization_id: str, file_asset_id: str):
        return self.asset


@pytest.mark.asyncio
async def test_ocr_rejects_quarantined_file() -> None:
    service = AccountingOcrService(session=None)  # type: ignore[arg-type]
    service.file_assets = _FileAssetRepository(
        type("FileAsset", (), {"status": "quarantined"})()
    )  # type: ignore[assignment]

    with pytest.raises(HTTPException) as exc_info:
        await service._ensure_file_ready_for_ocr(
            organization_id="org_1",
            file_asset_id="file_1",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "file_not_ready_for_ocr"


@pytest.mark.asyncio
async def test_upload_deletes_object_when_document_commit_fails(monkeypatch) -> None:
    class _Session:
        def __init__(self) -> None:
            self.rolled_back = False

        async def rollback(self) -> None:
            self.rolled_back = True

    class _Storage:
        def __init__(self) -> None:
            self.deleted = []

        async def delete(self, storage_key: str) -> None:
            self.deleted.append(storage_key)

    async def _create_file_asset(_self, _payload):
        return type(
            "FileAsset",
            (),
            {
                "id": "file_1",
                "content_hash": "hash_1",
                "storage_key": "org_1/file_1/invoice.pdf",
            },
        )()

    async def _fail_document_write(*_args, **_kwargs):
        raise RuntimeError("document commit failed")

    async def _valid_metadata(*_args, **_kwargs):
        return None

    session = _Session()
    storage = _Storage()
    service = AccountingDocumentService(session)  # type: ignore[arg-type]
    monkeypatch.setattr(FileService, "create_file_asset", _create_file_asset)
    monkeypatch.setattr(service, "create_metadata_document", _fail_document_write)
    monkeypatch.setattr(service, "_ensure_valid_metadata", _valid_metadata)

    with pytest.raises(RuntimeError, match="document commit failed"):
        await service.upload_document(
            organization_id="org_1",
            actor_user_id="user_1",
            client_company_id="client_1",
            document_type="invoice",
            category="sales",
            accounting_period="2026-05",
            file_name="invoice.pdf",
            mime_type="application/pdf",
            content=b"%PDF-1.7",
            storage=storage,  # type: ignore[arg-type]
        )

    assert session.rolled_back is True
    assert storage.deleted == ["org_1/file_1/invoice.pdf"]
