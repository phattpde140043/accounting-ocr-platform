from types import SimpleNamespace

import pytest

from app.domains.accounting.export_service import AccountingExportService
from app.domains.accounting.schemas import CreateExportBatchIn


def _document(document_id: str = "doc_1") -> SimpleNamespace:
    return SimpleNamespace(
        id=document_id,
        client_company_id="client_1",
        document_type="invoice",
        category="sales",
        accounting_period="2026-05",
        file_name="invoice.pdf",
        status="exported",
        seller_tax_code="0312345678",
        invoice_number="INV-1",
        invoice_symbol="AA/26",
        invoice_date="2026-05-01",
        total_amount="1250000",
    )


@pytest.mark.asyncio
async def test_download_export_batch_builds_artifact_with_batch_document_query() -> None:
    batch = SimpleNamespace(
        id="export_1",
        status="completed",
        format="misa",
        correlation_id="corr_1",
    )
    document_queries: list[list[str]] = []
    audit_events = []

    class _Session:
        committed = False

        async def commit(self) -> None:
            self.committed = True

    class _Batches:
        async def get_for_org(self, organization_id: str, batch_id: str):
            return batch

    class _Items:
        async def list_for_batch(self, organization_id: str, batch_id: str):
            return [SimpleNamespace(document_id="doc_1")]

    class _Documents:
        async def list_by_ids_for_org(
            self, organization_id: str, document_ids: list[str]
        ):
            document_queries.append(document_ids)
            return [_document()]

    class _AuditLog:
        async def record(self, event) -> None:
            audit_events.append(event)

    session = _Session()
    service = AccountingExportService(session=session)  # type: ignore[arg-type]
    service.batches = _Batches()  # type: ignore[assignment]
    service.items = _Items()  # type: ignore[assignment]
    service.documents = _Documents()  # type: ignore[assignment]
    service.audit_log = _AuditLog()  # type: ignore[assignment]

    artifact = await service.download_export_batch(
        organization_id="org_1",
        actor_user_id="user_1",
        batch_id="export_1",
    )

    assert artifact.file_name == "misa-export.csv"
    assert "INV-1" in artifact.content.decode("utf-8")
    assert document_queries == [["doc_1"]]
    assert batch.status == "downloaded"
    assert session.committed is True
    assert audit_events[0].action == "ExportDownloaded"
    assert audit_events[0].metadata == {"document_count": 1, "format": "misa"}


@pytest.mark.asyncio
async def test_repeated_download_is_idempotent() -> None:
    batch = SimpleNamespace(
        id="export_1",
        status="downloaded",
        format="json",
        correlation_id="corr_1",
    )

    class _Session:
        async def commit(self) -> None:
            return None

    class _Batches:
        async def get_for_org(self, organization_id: str, batch_id: str):
            return batch

    class _Items:
        async def list_for_batch(self, organization_id: str, batch_id: str):
            return [SimpleNamespace(document_id="doc_1")]

    class _Documents:
        async def list_by_ids_for_org(
            self, organization_id: str, document_ids: list[str]
        ):
            return [_document()]

    class _AuditLog:
        async def record(self, event) -> None:
            return None

    service = AccountingExportService(session=_Session())  # type: ignore[arg-type]
    service.batches = _Batches()  # type: ignore[assignment]
    service.items = _Items()  # type: ignore[assignment]
    service.documents = _Documents()  # type: ignore[assignment]
    service.audit_log = _AuditLog()  # type: ignore[assignment]

    artifact = await service.download_export_batch(
        organization_id="org_1",
        actor_user_id="user_1",
        batch_id="export_1",
    )

    assert artifact.file_name == "accounting-export.json"
    assert batch.status == "downloaded"


@pytest.mark.asyncio
async def test_create_export_batch_exports_each_document_once_and_records_completion() -> None:
    documents = [
        SimpleNamespace(id="doc_1", status="approved"),
        SimpleNamespace(id="doc_2", status="approved"),
    ]
    export_items = []
    audit_events = []

    class _Session:
        committed = False

        async def commit(self) -> None:
            self.committed = True

    class _Batches:
        async def get_by_idempotency_key(self, organization_id: str, key: str):
            return None

        async def add(self, batch) -> None:
            return None

    class _Items:
        async def add(self, item) -> None:
            export_items.append(item)

    class _Documents:
        async def list_by_ids_for_org(
            self, organization_id: str, document_ids: list[str]
        ):
            return documents

    class _AuditLog:
        async def record(self, event) -> None:
            audit_events.append(event)

    session = _Session()
    service = AccountingExportService(session=session)  # type: ignore[arg-type]
    service.batches = _Batches()  # type: ignore[assignment]
    service.items = _Items()  # type: ignore[assignment]
    service.documents = _Documents()  # type: ignore[assignment]
    service.audit_log = _AuditLog()  # type: ignore[assignment]

    result = await service.create_export_batch(
        organization_id="org_1",
        actor_user_id="user_1",
        payload=CreateExportBatchIn(
            document_ids=["doc_1", "doc_2"],
            format="json",
        ),
    )

    assert result["document_count"] == 2
    assert [item.document_id for item in export_items] == ["doc_1", "doc_2"]
    assert [document.status for document in documents] == ["exported", "exported"]
    assert [event.action for event in audit_events] == [
        "ExportBatchCreated",
        "ExportCompleted",
    ]
