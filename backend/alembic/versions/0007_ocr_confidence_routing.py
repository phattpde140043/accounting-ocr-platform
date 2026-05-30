"""ocr confidence routing

Revision ID: 0007_ocr_confidence_routing
Revises: 0006_durable_worker_claiming
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_ocr_confidence_routing"
down_revision = "0006_durable_worker_claiming"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounting_ocr_results",
        sa.Column(
            "review_route",
            sa.String(length=60),
            nullable=False,
            server_default="human_review",
        ),
    )
    op.add_column(
        "accounting_ocr_results",
        sa.Column("review_reasons", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_index(
        "ix_accounting_ocr_results_review_route",
        "accounting_ocr_results",
        ["review_route"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_accounting_ocr_results_review_route",
        "accounting_ocr_results",
    )
    op.drop_column("accounting_ocr_results", "review_reasons")
    op.drop_column("accounting_ocr_results", "review_route")
