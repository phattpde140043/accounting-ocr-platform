"""correlation ids

Revision ID: 0003_correlation_ids
Revises: 0002_duplicate_detection_fields
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_correlation_ids"
down_revision = "0002_duplicate_detection_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "background_jobs",
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
    )
    op.create_index(
        "ix_background_jobs_correlation_id",
        "background_jobs",
        ["correlation_id"],
    )

    op.add_column(
        "audit_events",
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
    )
    op.create_index(
        "ix_audit_events_correlation_id",
        "audit_events",
        ["correlation_id"],
    )

    op.add_column(
        "accounting_ocr_jobs",
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
    )
    op.create_index(
        "ix_accounting_ocr_jobs_correlation_id",
        "accounting_ocr_jobs",
        ["correlation_id"],
    )

    op.add_column(
        "accounting_export_batches",
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
    )
    op.create_index(
        "ix_accounting_export_batches_correlation_id",
        "accounting_export_batches",
        ["correlation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_accounting_export_batches_correlation_id",
        "accounting_export_batches",
    )
    op.drop_column("accounting_export_batches", "correlation_id")
    op.drop_index("ix_accounting_ocr_jobs_correlation_id", "accounting_ocr_jobs")
    op.drop_column("accounting_ocr_jobs", "correlation_id")
    op.drop_index("ix_audit_events_correlation_id", "audit_events")
    op.drop_column("audit_events", "correlation_id")
    op.drop_index("ix_background_jobs_correlation_id", "background_jobs")
    op.drop_column("background_jobs", "correlation_id")
