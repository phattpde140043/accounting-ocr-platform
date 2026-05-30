"""query budget indexes

Revision ID: 0004_query_budget_indexes
Revises: 0003_correlation_ids
Create Date: 2026-05-31
"""

from alembic import op


revision = "0004_query_budget_indexes"
down_revision = "0003_correlation_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_accounting_documents_org_status_client_period_created",
        "accounting_documents",
        [
            "organization_id",
            "status",
            "client_company_id",
            "accounting_period",
            "created_at",
        ],
    )
    op.create_index(
        "ix_accounting_documents_org_status_created",
        "accounting_documents",
        ["organization_id", "status", "created_at"],
    )
    op.create_index(
        "ix_audit_events_org_created",
        "audit_events",
        ["organization_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_org_created", "audit_events")
    op.drop_index(
        "ix_accounting_documents_org_status_created",
        "accounting_documents",
    )
    op.drop_index(
        "ix_accounting_documents_org_status_client_period_created",
        "accounting_documents",
    )
