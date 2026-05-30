"""durable worker claiming

Revision ID: 0006_durable_worker_claiming
Revises: 0005_idempotency_primitives
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_durable_worker_claiming"
down_revision = "0005_idempotency_primitives"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "background_jobs",
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="4"),
    )
    op.add_column(
        "background_jobs",
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "background_jobs",
        sa.Column("locked_by", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "background_jobs",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_background_jobs_available_at", "background_jobs", ["available_at"]
    )
    op.create_index("ix_background_jobs_locked_by", "background_jobs", ["locked_by"])
    op.create_index(
        "ix_background_jobs_locked_until", "background_jobs", ["locked_until"]
    )
    op.create_index(
        "ix_background_jobs_claimable",
        "background_jobs",
        ["status", "available_at", "attempts"],
    )


def downgrade() -> None:
    op.drop_index("ix_background_jobs_claimable", "background_jobs")
    op.drop_index("ix_background_jobs_locked_until", "background_jobs")
    op.drop_index("ix_background_jobs_locked_by", "background_jobs")
    op.drop_index("ix_background_jobs_available_at", "background_jobs")
    op.drop_column("background_jobs", "locked_until")
    op.drop_column("background_jobs", "locked_by")
    op.drop_column("background_jobs", "available_at")
    op.drop_column("background_jobs", "max_attempts")
