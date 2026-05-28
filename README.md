# Accounting OCR Platform

Standalone project for Câu 1: a document intake and OCR platform for accounting service companies in Vietnam.

## Scope

- Google SSO adapter, JWT sessions, RBAC and audit history.
- Client company management.
- Accounting document import metadata and lifecycle APIs.
- OCR provider boundary with mock and OpenAI-backed adapter.
- OCR review, approval and export batch workflows.
- Region OCR API and Chrome extension prototype.
- Admin user management, dashboards and traceable request logging.

## Architecture

The backend follows explicit bounded modules:

- `app.core`: configuration, database, auth context, permissions, storage and observability.
- `app.domains.platform`: users, organizations, memberships, auth and audit.
- `app.domains.shared`: file assets and background jobs.
- `app.domains.accounting`: client companies, documents, OCR, review and exports.
- `app.domains.dashboard`: accounting-focused dashboard aggregation.

The frontend is a NextJS app focused on accounting intake, OCR workflows, dashboards and admin.

## Local Run

Backend:

```bash
cd backend
python3 -m pip install -e '.[dev]'
uvicorn app.main:app --reload --port 8001
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --port 3001
```

Docker Compose:

```bash
docker compose up --build
```

Open:

- Backend: `http://localhost:8001/docs`
- Frontend: `http://localhost:3001`

## Verification

```bash
python3 -m compileall backend/app
python3 -m pytest backend/app/tests -q -m 'not integration'
```
