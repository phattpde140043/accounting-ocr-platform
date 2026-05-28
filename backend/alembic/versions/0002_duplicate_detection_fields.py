"""duplicate detection fields

Revision ID: 0002_duplicate_detection_fields
Revises: 0001_schema_backbone
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_duplicate_detection_fields"
down_revision = "0001_schema_backbone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "file_assets",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_file_assets_content_hash",
        "file_assets",
        ["content_hash"],
    )
    op.create_unique_constraint(
        "uq_file_assets_org_content_hash",
        "file_assets",
        ["organization_id", "content_hash"],
    )

    op.add_column(
        "accounting_documents",
        sa.Column("file_content_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "accounting_documents",
        sa.Column("seller_tax_code", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "accounting_documents",
        sa.Column("invoice_number", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "accounting_documents",
        sa.Column("invoice_symbol", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "accounting_documents",
        sa.Column("invoice_date", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "accounting_documents",
        sa.Column("total_amount", sa.String(length=80), nullable=True),
    )
    op.create_index(
        "ix_accounting_documents_file_content_hash",
        "accounting_documents",
        ["file_content_hash"],
    )
    op.create_index(
        "ix_accounting_documents_seller_tax_code",
        "accounting_documents",
        ["seller_tax_code"],
    )
    op.create_index(
        "ix_accounting_documents_invoice_number",
        "accounting_documents",
        ["invoice_number"],
    )
    op.create_index(
        "ix_accounting_documents_invoice_symbol",
        "accounting_documents",
        ["invoice_symbol"],
    )
    op.create_index(
        "ix_accounting_documents_invoice_date",
        "accounting_documents",
        ["invoice_date"],
    )
    op.create_index(
        "ix_accounting_documents_total_amount",
        "accounting_documents",
        ["total_amount"],
    )
    op.create_index(
        "ix_accounting_documents_invoice_identity",
        "accounting_documents",
        [
            "organization_id",
            "seller_tax_code",
            "invoice_number",
            "invoice_symbol",
            "invoice_date",
            "total_amount",
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_accounting_documents_invoice_identity", "accounting_documents")
    op.drop_index("ix_accounting_documents_total_amount", "accounting_documents")
    op.drop_index("ix_accounting_documents_invoice_date", "accounting_documents")
    op.drop_index("ix_accounting_documents_invoice_symbol", "accounting_documents")
    op.drop_index("ix_accounting_documents_invoice_number", "accounting_documents")
    op.drop_index("ix_accounting_documents_seller_tax_code", "accounting_documents")
    op.drop_index("ix_accounting_documents_file_content_hash", "accounting_documents")
    op.drop_column("accounting_documents", "total_amount")
    op.drop_column("accounting_documents", "invoice_date")
    op.drop_column("accounting_documents", "invoice_symbol")
    op.drop_column("accounting_documents", "invoice_number")
    op.drop_column("accounting_documents", "seller_tax_code")
    op.drop_column("accounting_documents", "file_content_hash")

    op.drop_constraint(
        "uq_file_assets_org_content_hash", "file_assets", type_="unique"
    )
    op.drop_index("ix_file_assets_content_hash", "file_assets")
    op.drop_column("file_assets", "content_hash")
