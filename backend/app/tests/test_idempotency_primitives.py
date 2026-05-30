from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.domains.accounting.export_service import (
    AccountingExportService,
    build_export_idempotency_key,
)
from app.domains.accounting.ocr_service import AccountingOcrService
from app.domains.accounting.schemas import CreateExportBatchIn


def test_export_idempotency_key_is_stable_for_document_order() -> None:
    first = build_export_idempotency_key(
        document_ids=["doc_2", "doc_1"],
        export_format="misa",
        requested_key=None,
    )
    second = build_export_idempotency_key(
        document_ids=["doc_1", "doc_2"],
        export_format="misa",
        requested_key=None,
    )

    assert first == second
    assert len(first) == 64


@pytest.mark.asyncio
async def test_repeated_export_request_returns_existing_batch() -> None:
    class _Batches:
        async def get_by_idempotency_key(self, organization_id: str, key: str):
            return SimpleNamespace(id="export_1", status="completed", format="misa")

    class _Items:
        async def list_for_batch(self, organization_id: str, batch_id: str):
            return [SimpleNamespace(id="item_1")]

    service = AccountingExportService(session=None)  # type: ignore[arg-type]
    service.batches = _Batches()  # type: ignore[assignment]
    service.items = _Items()  # type: ignore[assignment]

    result = await service.create_export_batch(
        organization_id="org_1",
        actor_user_id="user_1",
        payload=CreateExportBatchIn(document_ids=["doc_1"], format="misa"),
    )

    assert result == {
        "id": "export_1",
        "status": "completed",
        "format": "misa",
        "document_count": 1,
    }


@pytest.mark.asyncio
async def test_repeated_ocr_request_returns_existing_active_job() -> None:
    class _Documents:
        async def get_for_org(self, organization_id: str, document_id: str):
            return SimpleNamespace(file_asset_id="file_1")

    class _FileAssets:
        async def get_for_org(self, organization_id: str, file_asset_id: str):
            return SimpleNamespace(status="stored")

    class _OcrJobs:
        async def get_active_for_document_provider(self, **_kwargs):
            return SimpleNamespace(id="ocrjob_1", status="queued")

    class _BackgroundJobs:
        async def get_for_resource(self, *_args):
            return SimpleNamespace(id="job_1")

    service = AccountingOcrService(session=None)  # type: ignore[arg-type]
    service.documents = _Documents()  # type: ignore[assignment]
    service.file_assets = _FileAssets()  # type: ignore[assignment]
    service.ocr_jobs = _OcrJobs()  # type: ignore[assignment]
    service.background_jobs = _BackgroundJobs()  # type: ignore[assignment]

    result = await service.request_ocr(
        organization_id="org_1",
        actor_user_id="user_1",
        document_id="doc_1",
    )

    assert result == {
        "status": "queued",
        "ocr_job_id": "ocrjob_1",
        "background_job_id": "job_1",
    }


@pytest.mark.asyncio
async def test_stale_ocr_field_correction_is_rejected() -> None:
    class _OcrFields:
        async def get_for_org(self, organization_id: str, field_id: str):
            return SimpleNamespace(
                id="field_1",
                result_id="result_1",
                field_value="old",
                field_key="total_amount",
                source="ocr",
                version=2,
            )

    service = AccountingOcrService(session=None)  # type: ignore[arg-type]
    service.ocr_fields = _OcrFields()  # type: ignore[assignment]

    with pytest.raises(HTTPException) as exc_info:
        await service.update_field(
            organization_id="org_1",
            actor_user_id="user_1",
            result_id="result_1",
            field_id="field_1",
            value="new",
            version=1,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "stale_ocr_field_version"
