import inspect

import pytest

from app.domains.accounting.repositories import AccountingDocumentRepository
from app.domains.accounting.router import list_documents


def test_document_list_route_exposes_queue_filters_and_pagination() -> None:
    parameters = inspect.signature(list_documents).parameters

    assert "status" in parameters
    assert "client_company_id" in parameters
    assert "accounting_period" in parameters
    assert "limit" in parameters
    assert "offset" in parameters


class _EmptyScalarResult:
    def all(self) -> list[object]:
        return []


class _CapturingSession:
    def __init__(self) -> None:
        self.statement = None

    async def scalars(self, statement):
        self.statement = statement
        return _EmptyScalarResult()


@pytest.mark.asyncio
async def test_document_repository_queue_query_is_tenant_scoped_and_filtered() -> None:
    session = _CapturingSession()
    repository = AccountingDocumentRepository(session)  # type: ignore[arg-type]

    await repository.list_for_org(
        "org_1",
        status="needs_review",
        client_company_id="client_1",
        accounting_period="2026-05",
        limit=25,
        offset=50,
    )

    sql = str(session.statement.compile(compile_kwargs={"literal_binds": True}))

    assert "accounting_documents.organization_id = 'org_1'" in sql
    assert "accounting_documents.status = 'needs_review'" in sql
    assert "accounting_documents.client_company_id = 'client_1'" in sql
    assert "accounting_documents.accounting_period = '2026-05'" in sql
    assert "LIMIT 25" in sql
    assert "OFFSET 50" in sql
