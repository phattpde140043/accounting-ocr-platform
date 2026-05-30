from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.domains.accounting.region_ocr_service import RegionOcrService
from app.domains.accounting.schemas import RegionOcrIn


@pytest.mark.parametrize(
    "regions",
    [
        [],
        [{"page": 0, "x": 1, "y": 1, "width": 20, "height": 20}],
        [{"page": 1, "x": -1, "y": 1, "width": 20, "height": 20}],
        [{"page": 1, "x": 1, "y": 1, "width": 0, "height": 20}],
        [{"page": 1, "x": 1, "y": 1, "width": 5001, "height": 20}],
    ],
)
def test_region_ocr_rejects_invalid_or_oversized_regions(regions: list[dict]) -> None:
    with pytest.raises(ValidationError):
        RegionOcrIn(regions=regions)


@pytest.mark.asyncio
async def test_region_ocr_rejects_cross_tenant_document_reference() -> None:
    class _Documents:
        async def get_for_org(self, organization_id: str, document_id: str):
            return None

    service = RegionOcrService(session=None)  # type: ignore[arg-type]
    service.documents = _Documents()  # type: ignore[assignment]

    with pytest.raises(HTTPException) as exc_info:
        await service.process_regions(
            organization_id="org_1",
            actor_user_id="user_1",
            document_id="doc_other_tenant",
            payload=RegionOcrIn(
                regions=[{"page": 1, "x": 1, "y": 1, "width": 20, "height": 20}]
            ),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "document_not_found"


@pytest.mark.asyncio
async def test_region_ocr_audit_contains_only_region_count() -> None:
    events = []

    class _Session:
        async def commit(self) -> None:
            return None

    class _Documents:
        async def get_for_org(self, organization_id: str, document_id: str):
            return SimpleNamespace(id=document_id)

    class _AuditLog:
        async def record(self, event) -> None:
            events.append(event)

    service = RegionOcrService(session=_Session())  # type: ignore[arg-type]
    service.documents = _Documents()  # type: ignore[assignment]
    service.audit_log = _AuditLog()  # type: ignore[assignment]

    result = await service.process_regions(
        organization_id="org_1",
        actor_user_id="user_1",
        document_id="doc_1",
        payload=RegionOcrIn(
            regions=[{"page": 1, "x": 1, "y": 1, "width": 20, "height": 20}]
        ),
    )

    assert result["regions"][0]["text"] == "Mock OCR text for region 1"
    assert events[0].metadata == {"region_count": 1}
