# API Specification

This is the hand-maintained contract summary for the Accounting OCR Platform.
Run the backend and open `http://localhost:8001/docs` for generated OpenAPI.

## Base URL

`/api/v1`

Protected routes require `Authorization: Bearer <token>`. Local demo mode also
supports explicit demo headers when `ACCOUNTING_OCR_AUTH_MODE=demo`.

## Authentication

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/auth/google/login` | Return Google SSO metadata. |
| `POST` | `/auth/google/callback` | Verify Google ID token, resolve membership and issue JWT. |
| `GET` | `/me` | Return current tenant principal and permissions. |

Google callback request:

```json
{ "id_token": "<google-id-token>" }
```

## Client Companies

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/accounting/client-companies?limit=50&offset=0` | List tenant client companies. |
| `POST` | `/accounting/client-companies` | Create tenant client company. |

Create request:

```json
{ "name": "Acme Vietnam", "tax_code": "0312345678" }
```

## Documents And OCR

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/accounting/documents` | List documents with optional `status`, `client_company_id`, `accounting_period`, `limit`, `offset`. |
| `POST` | `/accounting/documents` | Create metadata-backed document. |
| `POST` | `/accounting/documents/upload` | Validate and upload PDF/JPG/PNG multipart file. |
| `POST` | `/accounting/documents/{document_id}/ocr-jobs` | Queue OCR idempotently. |
| `POST` | `/accounting/ocr-jobs/{ocr_job_id}/execute` | Execute queued OCR through provider boundary. |
| `GET` | `/accounting/documents/{document_id}/ocr-result` | Return normalized OCR result and field DTOs. |
| `PATCH` | `/accounting/ocr-results/{result_id}/fields/{field_id}` | Correct one field using optimistic version. |
| `POST` | `/accounting/ocr-results/{result_id}/approve` | Validate and approve OCR result. |

Multipart upload fields:

```text
file
client_company_id
accounting_period     YYYY-MM
document_type        invoice | receipt | credit_note | debit_note
category             sales | purchase | expense | other
```

Field correction request:

```json
{ "value": "1300000", "version": 1 }
```

OCR result includes `confidence_level`, `review_route`, `review_reasons` and
versioned `field_items`.

## Export

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/accounting/export-batches` | Create or reuse approved-document export batch. |
| `GET` | `/accounting/export-batches/{batch_id}/download` | Download audited JSON or CSV artifact. |

Create request:

```json
{
  "document_ids": ["doc_123"],
  "format": "misa",
  "idempotency_key": "optional-client-key"
}
```

Supported templates: `json`, `misa`, `fast`.

## Region OCR

`POST /accounting/documents/{document_id}/region-ocr`

```json
{
  "regions": [
    { "page": 1, "x": 10, "y": 20, "width": 400, "height": 120 }
  ]
}
```

Requests require an existing tenant-scoped document, one to ten regions,
positive coordinates and dimensions no greater than `5000`.

## Dashboard And Admin

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/dashboard/summary` | Return role-aware tenant operational metrics. |
| `GET` | `/dashboard/admin` | Return admin dashboard focus. |
| `GET` | `/dashboard/employee` | Return employee dashboard focus. |
| `GET` | `/admin/users?limit=50&offset=0` | List tenant users. |
| `POST` | `/admin/users` | Create tenant user membership. |
| `POST` | `/admin/users/{user_id}/reset-password` | Record password reset request. |
| `GET` | `/admin/audit-events?limit=50&offset=0` | List paginated safe audit events. |

Paginated list responses include:

```json
{
  "items": [],
  "page_info": {
    "limit": 50,
    "offset": 0,
    "next_offset": null,
    "has_next": false
  }
}
```
