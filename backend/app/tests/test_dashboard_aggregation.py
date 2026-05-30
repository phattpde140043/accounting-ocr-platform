from sqlalchemy.dialects import postgresql

from app.domains.accounting.models import AccountingDocument
from app.domains.dashboard.service import DashboardAggregationService


def test_dashboard_operational_query_is_tenant_scoped_and_aggregate_only() -> None:
    document_count = DashboardAggregationService._count(AccountingDocument, "org_1")
    sql = str(
        document_count.element.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )

    assert "count(*)" in sql.lower()
    assert "accounting_documents.organization_id = 'org_1'" in sql
