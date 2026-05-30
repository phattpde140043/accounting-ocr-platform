import { documents as fallbackDocuments } from "./demo-data";
import { apiDownload, apiGet, apiPatch, apiPost, apiPostForm } from "./api-client";

type ListResponse<T> = {
  items: T[];
};

export type AccountingDocument = {
  id: string;
  organization_id: string;
  client_company_id: string;
  document_type: string;
  category: string;
  accounting_period: string;
  file_name: string;
  file_content_hash?: string | null;
  mime_type: string;
  seller_tax_code?: string | null;
  invoice_number?: string | null;
  invoice_symbol?: string | null;
  invoice_date?: string | null;
  total_amount?: string | null;
  status: string;
  ocr_status: string;
  created_at: string;
};

export type UploadAccountingDocumentInput = {
  file: File;
  clientCompanyId: string;
  accountingPeriod: string;
  documentType: string;
  category: string;
};

export type AccountingDocumentListFilters = {
  status?: string;
  clientCompanyId?: string;
  accountingPeriod?: string;
  limit?: number;
  offset?: number;
};

export type AccountingDocumentRow = {
  id: string;
  company: string;
  type: string;
  status: string;
  period: string;
};

export type OcrField = {
  id: string;
  key: string;
  value: string | null;
  confidence: number;
  source: string;
  version: number;
};

export type OcrResult = {
  result_id: string | null;
  document_id: string;
  status: string;
  fields: Record<string, string | null>;
  field_items: OcrField[];
  confidence: number;
  confidence_level: string;
  review_route: string;
  review_reasons: string[];
};

export type UpdateOcrFieldInput = {
  resultId: string;
  fieldId: string;
  value: string;
  version: number;
};

export type ExportFormat = "json" | "misa" | "fast";

export type ExportBatch = {
  id: string;
  status: string;
  format: ExportFormat;
  document_count: number;
};

function buildDocumentListPath(filters: AccountingDocumentListFilters = {}): string {
  const params = new URLSearchParams();

  if (filters.status) {
    params.set("status", filters.status);
  }
  if (filters.clientCompanyId) {
    params.set("client_company_id", filters.clientCompanyId);
  }
  if (filters.accountingPeriod) {
    params.set("accounting_period", filters.accountingPeriod);
  }
  if (filters.limit !== undefined) {
    params.set("limit", String(filters.limit));
  }
  if (filters.offset !== undefined) {
    params.set("offset", String(filters.offset));
  }

  const query = params.toString();
  return query ? `/accounting/documents?${query}` : "/accounting/documents";
}

function mapDocumentToRow(document: AccountingDocument): AccountingDocumentRow {
  return {
    id: document.id,
    company: document.client_company_id,
    type: document.document_type,
    status: document.status,
    period: document.accounting_period
  };
}

function normalizeOcrResult(result: OcrResult): OcrResult {
  if (result.field_items.length > 0) {
    return result;
  }

  return {
    ...result,
    field_items: Object.entries(result.fields).map(([key, value]) => ({
      id: key,
      key,
      value,
      confidence: result.confidence,
      source: "ocr",
      version: 1
    }))
  };
}

export async function listAccountingDocuments(
  filters: AccountingDocumentListFilters = {}
): Promise<AccountingDocument[]> {
  const response = await apiGet<ListResponse<AccountingDocument>>(
    buildDocumentListPath(filters)
  );
  return response.items;
}

export async function getAccountingDocuments(
  filters: AccountingDocumentListFilters = {}
): Promise<AccountingDocumentRow[]> {
  try {
    const documents = await listAccountingDocuments(filters);
    return documents.map(mapDocumentToRow);
  } catch {
    return fallbackDocuments;
  }
}

export async function getReviewQueueDocuments(
  filters: Omit<AccountingDocumentListFilters, "status"> = {}
): Promise<AccountingDocument[]> {
  return listAccountingDocuments({
    ...filters,
    status: "needs_review"
  });
}

export async function getOcrResult(documentId: string): Promise<OcrResult> {
  const result = await apiGet<OcrResult>(
    `/accounting/documents/${documentId}/ocr-result`
  );
  return normalizeOcrResult(result);
}

export async function updateOcrField(
  input: UpdateOcrFieldInput
): Promise<{ field_value: string; source: string; version: number }> {
  return apiPatch<{ field_value: string; source: string; version: number }>(
    `/accounting/ocr-results/${input.resultId}/fields/${input.fieldId}`,
    { value: input.value, version: input.version }
  );
}

export async function approveOcrResult(resultId: string): Promise<OcrResult> {
  const result = await apiPost<OcrResult>(
    `/accounting/ocr-results/${resultId}/approve`
  );
  return normalizeOcrResult(result);
}

export async function uploadAccountingDocument(
  input: UploadAccountingDocumentInput
): Promise<AccountingDocument> {
  const formData = new FormData();
  formData.append("file", input.file);
  formData.append("client_company_id", input.clientCompanyId);
  formData.append("accounting_period", input.accountingPeriod);
  formData.append("document_type", input.documentType);
  formData.append("category", input.category);

  return apiPostForm<AccountingDocument>("/accounting/documents/upload", formData);
}

export async function createExportBatch(
  documentIds: string[],
  format: ExportFormat
): Promise<ExportBatch> {
  return apiPost<ExportBatch>("/accounting/export-batches", {
    document_ids: documentIds,
    format
  });
}

export async function downloadExportBatch(
  batchId: string
): Promise<{ blob: Blob; fileName: string }> {
  return apiDownload(`/accounting/export-batches/${batchId}/download`);
}
