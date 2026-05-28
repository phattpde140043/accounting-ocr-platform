# API Specification

This document provides a high-level overview of the core endpoints for the Accounting OCR Platform. For the full, interactive API specification, please run the backend locally and navigate to the OpenAPI documentation at `http://localhost:8001/docs`.

## Base URL
`/api/v1`

---

## 1. Accounting Documents

### `POST /accounting/documents/upload`
Uploads a physical or digital document for OCR processing.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data:**
- `file`: The binary file to upload (PDF, PNG, JPG).
- `client_company_id`: String
- `document_type`: String (e.g., `invoice`, `receipt`)
- `category`: String
- `accounting_period`: String (e.g., `2026-05`)

**Response:** (200 OK)
```json
{
  "id": "doc_12345",
  "organization_id": "org_abc",
  "client_company_id": "client_xyz",
  "document_type": "invoice",
  "category": "expenses",
  "accounting_period": "2026-05",
  "file_name": "invoice_may.pdf",
  "mime_type": "application/pdf",
  "status": "uploaded",
  "ocr_status": "not_started",
  "created_at": "2026-05-26T10:00:00Z"
}
```

### `GET /accounting/documents`
Lists documents for the current organization.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `status`: Optional document status filter.
- `client_company_id`: Optional client company filter.
- `accounting_period`: Optional accounting period filter.
- `limit`: Optional page size, default `50`, max `100`.
- `offset`: Optional offset, default `0`.

**Response:** (200 OK)
```json
{
  "items": [
    {
      "id": "doc_12345",
      "status": "needs_review",
      "ocr_status": "completed",
      "...": "..."
    }
  ],
  "page_info": {
    "next_cursor": null,
    "has_next": false
  }
}
```

### `POST /accounting/documents/{document_id}/transition`
Transitions a document's status (e.g., from `uploaded` to `queued` for OCR processing).

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Body:**
```json
{
  "next_status": "queued"
}
```

**Response:** (200 OK) Returns the updated document object.

---

## 2. OCR Processing (Internal)

OCR jobs are processed asynchronously by the background workers. However, direct triggering or status checking APIs are available within the accounting module.

### `POST /accounting/ocr/{document_id}/extract`
Triggers the extraction process manually.

**Response:** (200 OK)
```json
{
  "provider": "openai",
  "confidence": 0.95,
  "fields": [
    {
      "key": "total_amount",
      "value": "1250000",
      "confidence": 0.98
    }
  ]
}
```

### `POST /accounting/documents/{document_id}/ocr-jobs`
Queues OCR for a document.

**Response:** (200 OK)
```json
{
  "status": "queued",
  "ocr_job_id": "ocrjob_123",
  "background_job_id": "job_456"
}
```

### `POST /accounting/ocr-jobs/{ocr_job_id}/execute`
Executes a queued OCR job through the configured provider boundary.

**Response:** (200 OK)
```json
{
  "status": "completed",
  "ocr_job_id": "ocrjob_123",
  "ocr_result_id": "ocrresult_789"
}
```

### `GET /accounting/documents/{document_id}/ocr-result`
Returns the latest OCR result for a document.

**Response:** (200 OK)
```json
{
  "result_id": "ocrresult_789",
  "document_id": "doc_12345",
  "status": "needs_review",
  "confidence": 0.91,
  "fields": {
    "total_amount": "1250000"
  },
  "field_items": [
    {
      "id": "ocrfield_1",
      "key": "total_amount",
      "value": "1250000",
      "confidence": 0.86,
      "source": "ocr"
    }
  ]
}
```

### `PATCH /accounting/ocr-results/{result_id}/fields/{field_id}`
Updates one normalized OCR field during review.

**Body:**
```json
{
  "value": "1300000"
}
```

### `POST /accounting/ocr-results/{result_id}/approve`
Approves an OCR result and transitions the document to approved.

---

## 3. Platform & Auth (TBD)
Endpoints for `POST /platform/auth/login`, `GET /platform/users/me`, etc. are defined within the `app.domains.platform` domain. Refer to OpenAPI docs for the full schema.
