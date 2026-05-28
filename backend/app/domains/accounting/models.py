from sqlalchemy import ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.model_mixins import IdMixin, TenantMixin, TimestampMixin


class AccountingClientCompany(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "accounting_client_companies"
    __table_args__ = (
        UniqueConstraint("organization_id", "tax_code", name="uq_accounting_client_tax"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_code: Mapped[str | None] = mapped_column(String(80))
    address: Mapped[str | None] = mapped_column(Text)


class AccountingDocument(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "accounting_documents"
    __table_args__ = (
        Index(
            "ix_accounting_documents_invoice_identity",
            "organization_id",
            "seller_tax_code",
            "invoice_number",
            "invoice_symbol",
            "invoice_date",
            "total_amount",
        ),
    )

    client_company_id: Mapped[str] = mapped_column(
        ForeignKey("accounting_client_companies.id"), index=True, nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    accounting_period: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    file_asset_id: Mapped[str | None] = mapped_column(String(120), index=True)
    file_content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    seller_tax_code: Mapped[str | None] = mapped_column(String(80), index=True)
    invoice_number: Mapped[str | None] = mapped_column(String(120), index=True)
    invoice_symbol: Mapped[str | None] = mapped_column(String(120), index=True)
    invoice_date: Mapped[str | None] = mapped_column(String(20), index=True)
    total_amount: Mapped[str | None] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    ocr_status: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class AccountingOcrJob(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "accounting_ocr_jobs"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("accounting_documents.id"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(120), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class AccountingOcrResult(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "accounting_ocr_results"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("accounting_documents.id"), index=True, nullable=False
    )
    job_id: Mapped[str] = mapped_column(ForeignKey("accounting_ocr_jobs.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class AccountingOcrField(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "accounting_ocr_fields"

    result_id: Mapped[str] = mapped_column(
        ForeignKey("accounting_ocr_results.id"), index=True, nullable=False
    )
    field_key: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    field_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    source: Mapped[str] = mapped_column(String(40), default="ocr", nullable=False)


class AccountingExportBatch(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "accounting_export_batches"

    status: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(40), default="json", nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(120), index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class AccountingExportItem(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "accounting_export_items"

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("accounting_export_batches.id"), index=True, nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("accounting_documents.id"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
