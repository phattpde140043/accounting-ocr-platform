from typing import Literal

from pydantic import BaseModel, Field


class ClientCompanyOut(BaseModel):
    id: str
    organization_id: str
    name: str
    tax_code: str | None = None
    created_at: str


class CreateClientCompanyIn(BaseModel):
    name: str
    tax_code: str | None = None


class AccountingDocumentOut(BaseModel):
    id: str
    organization_id: str
    client_company_id: str
    document_type: str
    category: str
    accounting_period: str
    file_name: str
    file_content_hash: str | None = None
    mime_type: str
    seller_tax_code: str | None = None
    invoice_number: str | None = None
    invoice_symbol: str | None = None
    invoice_date: str | None = None
    total_amount: str | None = None
    status: str
    ocr_status: str
    created_at: str


class CreateAccountingDocumentIn(BaseModel):
    client_company_id: str
    document_type: Literal["invoice", "receipt", "credit_note", "debit_note"] = "invoice"
    category: Literal["sales", "purchase", "expense", "other"] = "sales"
    accounting_period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    file_name: str
    mime_type: str
    file_asset_id: str | None = None
    file_content_hash: str | None = None


class OcrFieldOut(BaseModel):
    id: str
    key: str
    value: str | None = None
    confidence: float
    source: str
    version: int


class OcrResultOut(BaseModel):
    document_id: str
    status: str
    fields: dict
    field_items: list[OcrFieldOut] = Field(default_factory=list)
    confidence: float
    confidence_level: str = "medium"
    review_route: str = "human_review"
    review_reasons: list[str] = Field(default_factory=list)
    result_id: str | None = None


class UpdateOcrFieldIn(BaseModel):
    value: str
    version: int = Field(ge=1)


class CreateExportBatchIn(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=1000)
    format: str = "json"
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=120)


class ExportBatchOut(BaseModel):
    id: str
    status: str
    format: str
    document_count: int


class BoundingBoxIn(BaseModel):
    page: int = Field(default=1, ge=1, le=10000)
    x: float = Field(ge=0, le=100000)
    y: float = Field(ge=0, le=100000)
    width: float = Field(gt=0, le=5000)
    height: float = Field(gt=0, le=5000)


class RegionOcrIn(BaseModel):
    regions: list[BoundingBoxIn] = Field(min_length=1, max_length=10)


class RegionOcrRegionOut(BaseModel):
    page: int
    text: str
    confidence: float
    box: BoundingBoxIn


class RegionOcrOut(BaseModel):
    document_id: str
    regions: list[RegionOcrRegionOut]



class OcrJobRequestOut(BaseModel):
    status: str
    ocr_job_id: str
    background_job_id: str


class OcrJobExecutionOut(BaseModel):
    status: str
    ocr_job_id: str
    ocr_result_id: str
