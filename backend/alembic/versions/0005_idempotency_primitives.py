"""idempotency primitives

Revision ID: 0005_idempotency_primitives
Revises: 0004_query_budget_indexes
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_idempotency_primitives"
down_revision = "0004_query_budget_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_accounting_ocr_jobs_active_request",
        "accounting_ocr_jobs",
        ["organization_id", "document_id", "provider"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'processing')"),
    )
    op.add_column(
        "accounting_ocr_fields",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "accounting_export_batches",
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_accounting_export_batches_idempotency_key",
        "accounting_export_batches",
        ["idempotency_key"],
    )
    op.create_unique_constraint(
        "uq_accounting_export_batch_idempotency",
        "accounting_export_batches",
        ["organization_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_accounting_export_batch_idempotency",
        "accounting_export_batches",
        type_="unique",
    )
    op.drop_index(
        "ix_accounting_export_batches_idempotency_key",
        "accounting_export_batches",
    )
    op.drop_column("accounting_export_batches", "idempotency_key")
    op.drop_column("accounting_ocr_fields", "version")
    op.drop_index("uq_accounting_ocr_jobs_active_request", "accounting_ocr_jobs")
