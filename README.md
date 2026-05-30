# Accounting OCR Platform

Accounting OCR Platform is a modular document intake, OCR review, and export
system for accounting service teams that process invoices and supporting
documents for multiple client companies.

The platform is designed around a secure review workflow: upload accounting
documents, run OCR extraction, validate extracted fields, approve records, and
export accounting-ready data with traceable audit history.

## Repository Description

AI-assisted accounting document processing platform with FastAPI, Next.js,
multi-tenant RBAC, OCR provider abstraction, field-level review, audit logging,
and export workflows.

Suggested GitHub topics:

```text
fastapi, nextjs, accounting, ocr, document-processing, multi-tenant, rbac,
audit-log, python, typescript, vietnam-accounting
```

## Highlights

- Multi-tenant organization and client-company model.
- Google SSO adapter, JWT session context, RBAC and permission checks.
- Accounting document lifecycle from upload to approval and export.
- Secure upload validation for MIME type, extension, file signature and size.
- Duplicate detection via file hash and invoice identity fields.
- OCR provider boundary with mock and OpenAI-backed implementations.
- OCR result contract with field IDs for field-by-field correction.
- Reviewer queue UI with filters, versioned field correction and approval.
- Export templates and audited downloads for JSON, MISA-style CSV and FAST-style CSV.
- Canonical audit events, safe metadata validation and operational dashboard signals.
- Chrome extension workflow with explicit active-page region selection.

## Architecture

The backend is a FastAPI modular monolith organized by bounded context:

- `app.core`: configuration, database, request context, permissions, storage
  validation and observability.
- `app.domains.platform`: organizations, users, memberships, roles, auth and
  audit logs.
- `app.domains.shared`: file assets and background job orchestration.
- `app.domains.accounting`: client companies, documents, OCR, review,
  lifecycle policy and exports.
- `app.domains.dashboard`: accounting-focused dashboard aggregation.

The frontend is a Next.js application for operational workflows:

- `/dashboard`: accounting dashboard surface.
- `/accounting`: document intake and upload.
- `/accounting/review`: reviewer queue and OCR result inspection.
- `/admin`: administrative surface.
- `/ai`: AI/OCR workflow surface.

Detailed architecture notes are maintained in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and implementation planning is
tracked in [`docs/PLAN.md`](docs/PLAN.md).

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Frontend | Next.js, React, TypeScript |
| Database | PostgreSQL in production-like deployments |
| Auth | Google SSO adapter, JWT context, RBAC |
| OCR | Provider abstraction with mock and OpenAI adapters |
| Tooling | Pytest, ESLint, Docker Compose |

## Repository Structure

```text
backend/       FastAPI application, domain modules, Alembic migrations and tests
frontend/      Next.js application for intake, review, dashboard and admin UI
extension/     Chrome extension prototype for region OCR capture
docs/          Architecture, API contract and master implementation plan
infra/         Infrastructure placeholder for deployment assets
scripts/       Project-level operational scripts
```

## Local Development

Copy environment defaults:

```bash
cp .env.example .env
```

Start the stack with Docker Compose:

```bash
docker compose up --build
```

Backend only:

```bash
cd backend
python3 -m pip install -e '.[dev]'
alembic upgrade head
python -m scripts.seed_demo
uvicorn app.main:app --reload --port 8001
```

Frontend only:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api/v1 npm run dev -- --port 3001
```

Open:

- API docs: `http://localhost:8001/docs`
- Frontend: `http://localhost:3001`

Demo request headers:

```text
X-Organization-Id: org_demo
X-User-Id: user_admin
X-Role: admin
```

Demo headers are accepted only when `ACCOUNTING_OCR_ENVIRONMENT` is `local` or
`test` and `ACCOUNTING_OCR_AUTH_MODE=demo`. Production mode requires bearer JWT.

## Verification

Backend:

```bash
cd backend
python3 -m compileall app
python3 -m pytest app/tests -q -m 'not integration'
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Security And Privacy Notes

- Tenant isolation is enforced through organization-scoped repositories and
  request context.
- Uploads are validated before storage and duplicate files are detected by
  content hash.
- Formula injection is mitigated for spreadsheet-like CSV export templates.
- OCR provider payloads are not exposed through the normal frontend OCR result
  contract.
- Correlation IDs and audit logs provide traceability across background jobs,
  OCR execution and exports.

## Roadmap

- Add correction-history rendering from audit events.
- Add production object storage and external queue infrastructure.
- Expand accounting export formats and reconciliation validations.
- Add end-to-end browser tests for upload, OCR review and export journeys.
- Add packaged Chrome extension release verification and production API origin.

## License

No license has been published yet. Add a license before using this project in
public or commercial distributions.
