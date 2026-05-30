import inspect

import pytest

from app.domains.accounting.router import list_client_companies, list_documents
from app.domains.platform.admin_service import AdminUserService
from app.domains.platform.repositories import AuditEventRepository
from app.domains.platform.router import list_audit_events, list_users
from app.domains.shared.schemas import build_offset_page_info


@pytest.mark.parametrize(
    "route",
    [list_client_companies, list_documents, list_users, list_audit_events],
)
def test_table_list_routes_expose_bounded_offset_pagination(route) -> None:
    parameters = inspect.signature(route).parameters

    assert "limit" in parameters
    assert "offset" in parameters


def test_offset_page_info_exposes_next_page_when_page_is_full() -> None:
    page_info = build_offset_page_info(item_count=25, limit=25, offset=50)

    assert page_info.limit == 25
    assert page_info.offset == 50
    assert page_info.next_offset == 75
    assert page_info.has_next is True


def test_offset_page_info_ends_when_page_is_partial() -> None:
    page_info = build_offset_page_info(item_count=3, limit=25, offset=50)

    assert page_info.next_offset is None
    assert page_info.has_next is False


class _EmptyScalarResult:
    def all(self) -> list[object]:
        return []


class _CapturingSession:
    def __init__(self) -> None:
        self.statement = None

    async def scalars(self, statement):
        self.statement = statement
        return _EmptyScalarResult()

    async def execute(self, statement):
        self.statement = statement
        return _EmptyScalarResult()


@pytest.mark.asyncio
async def test_audit_repository_query_is_tenant_scoped_and_bounded() -> None:
    session = _CapturingSession()
    repository = AuditEventRepository(session)  # type: ignore[arg-type]

    await repository.list_recent_for_org("org_1", limit=25, offset=50)

    sql = str(session.statement.compile(compile_kwargs={"literal_binds": True}))

    assert "audit_events.organization_id = 'org_1'" in sql
    assert "LIMIT 25" in sql
    assert "OFFSET 50" in sql


@pytest.mark.asyncio
async def test_admin_user_query_is_tenant_scoped_and_bounded() -> None:
    session = _CapturingSession()
    service = AdminUserService(session)  # type: ignore[arg-type]

    await service.list_users("org_1", limit=20, offset=40)

    sql = str(session.statement.compile(compile_kwargs={"literal_binds": True}))

    assert "memberships.organization_id = 'org_1'" in sql
    assert "LIMIT 20" in sql
    assert "OFFSET 40" in sql
