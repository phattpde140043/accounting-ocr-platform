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
    document_type: str = "invoice"
    category: str = "sales"
    accounting_period: str
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


class OcrResultOut(BaseModel):
    document_id: str
    status: str
    fields: dict
    field_items: list[OcrFieldOut] = Field(default_factory=list)
    confidence: float
    result_id: str | None = None


class UpdateOcrFieldIn(BaseModel):
    value: str


class CreateExportBatchIn(BaseModel):
    document_ids: list[str]
    format: str = "json"


class ExportBatchOut(BaseModel):
    id: str
    status: str
    format: str
    document_count: int


class BoundingBoxIn(BaseModel):
    page: int = 1
    x: float
    y: float
    width: float
    height: float


class RegionOcrIn(BaseModel):
    regions: list[BoundingBoxIn]


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
