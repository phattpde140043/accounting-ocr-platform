# Accounting OCR Platform Plan

## Completed Backbone

- Platform identity, tenant context, RBAC and audit log.
- Accounting document import APIs and lifecycle.
- File storage abstraction.
- Background job abstraction and worker process.
- OCR provider interface, mock provider and OpenAI adapter.
- OCR review and export batch workflows.
- Accounting dashboard APIs.
- NextJS app shell with accounting forms.
- Chrome extension prototype for region OCR.
- Docker, CI baseline and backend tests.

## Architecture Reading Summary

The documented target architecture is a modular monolith:

- `app.core`: configuration, database, auth context, permissions, storage and observability.
- `app.domains.platform`: users, organizations, memberships, auth and audit.
- `app.domains.shared`: file assets and background jobs.
- `app.domains.accounting`: client companies, documents, OCR, review and exports.
- `app.domains.dashboard`: accounting-focused dashboard aggregation.

The end-to-end product flow is:

1. Browser, NextJS app or Chrome extension calls FastAPI under `/api/v1`.
2. FastAPI resolves tenant and user context, applies RBAC, validates accounting metadata and stores private document assets.
3. OCR work is executed asynchronously through the background job boundary.
4. OCR providers return normalized VN accounting fields and confidence data.
5. Accountants review machine output field by field, approve documents and export batches.
6. Admin users inspect audit history, dashboard metrics and OCR traceability.

The master plan already covers the technical backbone, but the next depth items need to be expanded into dependency-ordered implementation tasks so another agent can execute them safely.

## Master Plan Gap Analysis

- Upload depth gap: the API supports document upload semantics, but the frontend still needs production-grade multipart file intake, progress, validation and retry behavior.
- Review depth gap: OCR review and export workflows exist at the backend level, but the reviewer queue needs a field-by-field correction surface, confidence display and correction history UX.
- Confidence gap: OCR confidence is available conceptually, but low-confidence fields need UI emphasis and deterministic routing into review states.
- Export depth gap: export batch workflows exist, but MISA/FAST oriented templates need explicit generation, download UX and regression coverage.
- Auth hardening gap: Google SSO exists in demo and production-like modes, but callback/session hardening and tenant-safe invite/login flows need tightening before production use.
- Observability gap: traceable request logging is in scope, but upload, OCR, review and export flows need consistent logs and dashboard-visible operational signals.

## Planning Header

### Assumptions

- `docs/PLAN.md` is the current master plan.
- The completed backbone items are trusted as already implemented unless code verification later proves otherwise.
- The next agent should execute tasks sequentially, because each task feeds UX, data or test assumptions into the next one.
- Scope remains the standalone Accounting OCR Platform for Vietnamese accounting service companies.

### Diamond Standard Audit

- Scalable: tasks preserve the modular monolith boundaries and defer heavy OCR work to background jobs.
- Secure: every task includes tenant isolation, RBAC and private asset handling checks.
- Aesthetic: frontend tasks require accounting-workflow-specific UI, not generic upload or review screens.

### BFRI Risk Gate

- Architectural Fit: 5
- Testability: 4
- Complexity: 3
- Data Risk: 3
- Operational Risk: 2
- BFRI: `(5 + 4) - (3 + 3 + 2) = 1`
- Action: proceed only with explicit tests, monitoring hooks and isolation strategy in every task.

## Current Task Status Review - 2026-05-28

Verification performed:

- Backend compile: passed with `python3 -m compileall backend/app`.
- Backend unit tests: passed with `python3 -m pytest backend/app/tests -q -m 'not integration'` (`6 passed, 1 deselected`).
- Frontend build/lint: passed after installing dependencies with `npm install`; `npm run lint` and `npm run build` pass.

| Task | Status | Evidence | Next Action |
| --- | --- | --- | --- |
| Task 1: Audit Actual Backend And Frontend Surfaces | Done | Backend and frontend surfaces were mapped against docs. Backend has domain modules for platform, shared, accounting and dashboard. Frontend currently has shell pages and metadata-only accounting form. | Keep this status updated if new files are added before execution continues. |
| Task 2: Implement Production Multipart Upload UI | Done | Backend upload is bounded and validates MIME, extension, signature, safe filename and duplicate file hash. Frontend posts real multipart form data, validates file type/size, shows selected/uploading/success/error states and refreshes the document list after upload. | Continue to reviewer queue and field correction workflow. |
| Task 3: Build Reviewer Queue And Field-by-Field Correction UI | Partial | Backend has OCR result fetch, field update and approval endpoints plus audit events. Frontend has no reviewer queue, no selected-document workbench, no document preview, no field editor and no correction history UI. | Build review route/components and wire to existing OCR result APIs. |
| Task 4: Add OCR Confidence Visualization And Review Routing | Partial | OCR result and field confidence are persisted, and mock/OpenAI providers normalize confidence. All completed OCR currently routes to `needs_review`; there is no threshold policy, low/medium/high visual treatment, low-confidence queue filter or dashboard metric. | Add domain confidence thresholds, routing tests and UI badges/filters. |
| Task 5: Implement MISA And FAST Export Templates | Partial | Backend export batch validates approved documents and records export items, but download returns JSON-shaped document metadata. There are no MISA/FAST serializers, generated CSV/Excel files, template selector or frontend export workflow. | Add explicit export template enum/serializers and frontend download controls. |
| Task 6: Harden Production Google SSO Callback And Session Flow | Partial | Backend has demo and Google token verifier modes, callback endpoint and membership resolution. Demo header auth is still accepted whenever bearer auth is absent; there are no auth hardening tests, frontend callback states or SSO audit events. | Lock production auth behavior behind explicit config, add tests and callback UI. |
| Task 7: Add End-to-End Operational Traceability | Partial | Trace ID middleware works and service-level audit events exist for document creation/status, OCR request/completion/failure, field update, result approval, export batch creation and background jobs. Missing pieces include audit tests for the full workflow, upload-specific action naming, export download audit, dashboard/admin operational signals and payload leakage tests. | Standardize event names/payloads and add audit/dashboard coverage. |
| Task 8: Final Verification And Documentation Sync | Partial | Backend compile and unit tests pass. Frontend verification is blocked by missing dependencies. API spec is stale for some real endpoints, such as `/documents/{id}/ocr-jobs`, `/ocr-jobs/{id}/execute`, `/ocr-results/{id}/fields/{field_id}` and `/export-batches`. | Install frontend deps, run frontend checks, then sync `docs/api-spec.md` and architecture docs. |

## Planning And Review Assessment - Security/Performance Addendum

This review uses the planning, review and security skill chain against the current code and plan. It does not replace implementation tasks; it raises security and performance gates that must be handled before product-depth work is considered production-ready.

### Review Verdict

- Readiness score: 72/100.
- Verdict: REQUEST CHANGES before production rollout.
- Reason: the plan is well ordered, but it must make several security/performance controls explicit so agents do not ship a polished workflow on top of risky defaults.

### Severity-Ordered Findings

| Severity | Finding | Current Evidence | Required Plan Response |
| --- | --- | --- | --- |
| High | Production auth can silently fall back to demo header auth when bearer auth is missing. | `get_auth_provider` returns `DemoHeaderAuthProvider` whenever no bearer token exists. | Task 6 must block production mode on missing/invalid bearer auth and test demo-only behavior. |
| High | Upload path reads the full file into memory before validation and trusts client MIME type. | `upload_document` calls `await file.read()` before `FileService.validate_upload`; validation checks MIME and size after bytes are loaded. | Task 2 must add backend upload hardening before expanding frontend upload usage. |
| High | OCR/raw provider payload and audit metadata can leak sensitive accounting data if rendered or logged broadly. | OCR results store `raw_payload`; audit events store metadata JSON; admin audit UI is planned. | Tasks 3, 4 and 7 must add explicit safe serialization and leakage tests. |
| Medium | List and dashboard APIs need explicit pagination/filter contracts before reviewer/export UI scales. | `BaseRepository.list_for_org` has default limit/offset, but routers do not expose pagination/filter parameters. | Tasks 3, 4, 7 and 8 must specify query contracts and avoid unbounded UI reads. |
| Medium | Export download has an N+1 pattern and no generated artifact contract yet. | `download_export_batch` loops export items and fetches documents one by one. | Task 5 must add batched/projection query and artifact download contract. |
| Medium | Storage key uses original filename inside path and no content hash/duplicate detection gate is planned. | `FileService` builds `organization_id/file_id/original_name`; architecture requires duplicate prevention. | Task 2 must add sanitized names, content hash and duplicate detection planning. |
| Medium | CORS and security headers are not production-configurable in the current plan. | `main.py` hard-codes `http://localhost:3000`; no response security header task exists. | Task 6 or 8 must add environment-driven CORS/security header verification. |

### Mandatory Gates For Every Remaining Implementation Task

- Tenant gate: every backend query or mutation must use backend-resolved `organization_id`; no frontend-supplied tenant values.
- RBAC gate: all upload, review, approval, export, admin and audit endpoints must have role or permission tests.
- Data minimization gate: frontend payloads must not include raw OCR provider payloads, raw file bytes, tokens or export row contents unless explicitly required.
- Pagination gate: any list used by frontend tables/queues must have a documented limit, offset/cursor and bounded default.
- Performance gate: any batch operation must avoid per-row database fetches when a single tenant-scoped query can be used.
- Upload gate: file type, size, extension, content signature, storage key safety and duplicate detection must be checked server-side.
- Audit gate: audit events must prove action traceability without storing sensitive document text, tokens or raw provider prompts.
- Verification gate: backend tests must pass before frontend workflow signoff; frontend build/lint must be run once dependencies are available.

## Backend Architect Review Addendum

This review uses the `backend-architect` and `system-architecture` skill chain. It focuses on architectural fit rather than code-level polish.

### Architecture Verdict

- Architecture readiness score: 76/100.
- Verdict: REQUEST ARCHITECTURE CHANGES before broad feature execution.
- Reason: the modular monolith direction is sound, but several architectural contracts are implicit. The plan needs explicit ADRs, API contracts, state-machine ownership, provider dependency boundaries and data migration decisions so implementation agents do not create accidental coupling.

### Architecture Findings

| Severity | Finding | Current Evidence | Required Plan Response |
| --- | --- | --- | --- |
| High | OCR provider selection is not architecturally injected. | `AccountingOcrService.execute_ocr_job` instantiates `MockOcrProvider()` directly even though the architecture names mock and OpenAI adapters. | Add provider registry/dependency boundary before expanding OCR confidence/review flows. |
| High | Document/OCR/export lifecycle transitions are service-local and partially string-based. | Services assign statuses as strings; lifecycle validation is used for document transitions but OCR/export paths mutate status directly. | Add a domain lifecycle policy covering document, OCR job, OCR result and export batch transitions. |
| High | File asset and duplicate detection model is incomplete for the documented architecture. | File assets store name/key/size/mime, but no content hash or invoice identity duplicate fields exist. | Add data model/migration plan for content hash and invoice identity duplicate checks. |
| Medium | API contracts are DTO-shaped but not stable enough for frontend workflow work. | OCR result response returns a field dictionary without field IDs, while update requires `field_id`; list routes hide pagination/filter contracts. | Add API contract ADR and schema tests before UI implementation. |
| Medium | Background job architecture differs from docs and needs an explicit decision. | Docs mention Celery/Redis; code has a local background job abstraction and worker script. | Add ADR choosing current worker abstraction vs Celery/Redis and define retry/idempotency behavior. |
| Medium | Export generation lacks an architectural boundary for serializers, artifacts and batch sizing. | `AccountingExportService` currently owns validation, status changes and download shape. | Add export domain interface/serializer boundary and async threshold decision. |
| Medium | Platform admin and organization reads mix persistent DB and in-memory store patterns. | `/organizations` returns `store.organizations`, while admin users/audit use DB services. | Add plan task to remove or explicitly isolate demo store from production platform APIs. |
| Medium | Observability is trace/log/audit oriented but lacks correlation across background jobs. | HTTP middleware emits trace IDs; background job/audit payloads do not clearly carry a correlation ID. | Add correlation ID propagation through upload -> OCR job -> review -> export. |

### Architectural Principles To Enforce

- Modular monolith first: keep `platform`, `shared`, `accounting` and `dashboard` boundaries explicit; no generic `utils` or cross-domain shortcuts.
- Dependency rule: routers call services, services call repositories/providers; providers/storage/workers are injected or resolved through bounded registries.
- DTO-first: frontend-facing responses must be explicit schemas, never ORM models or raw provider payloads.
- State-machine ownership: all status transitions go through domain policy functions with tests.
- Idempotency: OCR request, OCR job execution and export batch creation must tolerate retry without duplicate side effects.
- Migration discipline: any new persistence field must include Alembic migration, seed/demo data update and rollback-safe defaults.
- Architecture documentation: major decisions require lightweight ADRs in `docs/ARCHITECTURE.md` or a dedicated docs ADR section before implementation is considered complete.

## Architecture Gate Subtasks

Run these architecture gates before continuing beyond Task 2. They are intentionally small and decision-oriented so implementation agents can keep moving without redesigning mid-task.

#### AG-1 Record architecture ADRs for current divergence
- Status: Done
- JTBD: As a future maintainer, I need documented decisions for worker, storage, OCR provider and export architecture.
- Description: Add lightweight ADR notes for current architecture choices and known divergences from `docs/ARCHITECTURE.md`.
- Implementation:
  - Record whether the project is using the local background job abstraction now or moving to Celery/Redis later.
  - Record storage strategy: local provider now, S3/MinIO-compatible provider boundary later.
  - Record OCR provider strategy: provider registry with mock/OpenAI adapters.
  - Record export strategy: synchronous small exports and background large exports, if selected.
- Acceptance Criteria:
  - ADRs list context, decision, alternatives, trade-offs and impact.
  - Architecture docs no longer imply Celery/Redis is already implemented if code keeps local workers.
  - Each ADR names the module boundary it affects.

#### AG-2 Define domain lifecycle policy
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `14 passed, 1 deselected`.
- Note: run backend tests from `backend/` or with `PYTHONPATH=backend`; running root-level pytest can import a stale editable `app` package from another workspace.
- JTBD: As an implementation agent, I need one source of truth for legal document/OCR/export status transitions.
- Description: Centralize lifecycle rules for accounting documents, OCR jobs/results and export batches.
- Implementation:
  - Inventory all current status strings and direct mutations.
  - Define allowed transitions in domain policy functions.
  - Add tests for valid and invalid transitions.
  - Update task descriptions to require services to call lifecycle policy rather than assigning arbitrary strings.
- Acceptance Criteria:
  - Document, OCR job/result and export batch statuses have explicit allowed transitions.
  - Services cannot approve/export invalid states without a tested policy path.
  - Existing lifecycle tests are expanded beyond two document cases.

#### AG-3 Define OCR provider registry boundary
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `17 passed, 1 deselected`.
- JTBD: As an OCR platform maintainer, I need provider selection to be configurable and testable.
- Description: Replace direct provider construction assumptions with a provider registry/factory boundary.
- Implementation:
  - Define how `mock`, `openai` and future providers are selected.
  - Ensure provider selection is tenant-safe and not freely user-controlled unless authorized.
  - Add tests that `execute_ocr_job` uses the provider recorded on the job.
  - Keep provider raw payload handling behind service serialization rules.
- Acceptance Criteria:
  - OCR service no longer needs direct knowledge of concrete provider constructors in core execution flow.
  - Provider selection has tests.
  - Unknown provider names fail closed.

#### AG-4 Define file asset and duplicate detection data model
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `20 passed, 1 deselected`.
- JTBD: As an accountant, I need duplicate invoices blocked reliably without expensive ad hoc scans.
- Description: Add a persistence and indexing plan for file hash and invoice identity duplicate checks.
- Implementation:
  - Add or plan `content_hash` on file assets/documents with tenant-scoped uniqueness where appropriate.
  - Define invoice identity fields from OCR/review data: seller tax code, invoice number, invoice symbol, invoice date and total amount.
  - Define indexes or unique constraints that support duplicate checks without full scans.
  - Include migration and seed data updates.
- Acceptance Criteria:
  - Duplicate detection can run with indexed tenant-scoped queries.
  - File-hash duplicate can be detected before OCR.
  - Invoice-identity duplicate can be detected after OCR/review when fields exist.

#### AG-5 Stabilize API contract and pagination architecture
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `22 passed, 1 deselected`.
- JTBD: As a frontend agent, I need stable schemas and pagination before building queue-heavy screens.
- Description: Define list, detail and mutation contracts for documents, OCR results, audit events and exports.
- Implementation:
  - Decide offset vs cursor pagination for current scale; use offset initially unless a cursor need is proven.
  - Add query parameters to API spec for list filters and page size.
  - Ensure OCR result contract exposes field IDs through DTOs.
  - Add schema tests for frontend-critical response shapes.
- Acceptance Criteria:
  - Frontend does not need to infer IDs from dictionaries or raw payloads.
  - Every table/queue endpoint has bounded pagination documented.
  - API spec matches router behavior before UI tasks depend on it.

#### AG-6 Define export architecture boundary
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `26 passed, 1 deselected`.
- JTBD: As an implementation agent, I need export template work isolated from document lifecycle and download transport.
- Description: Split export concerns into template serialization, artifact generation/storage and batch lifecycle.
- Implementation:
  - Define serializer interfaces/functions for `json`, `misa` and `fast`.
  - Define artifact storage or streaming strategy.
  - Define sync/async threshold and idempotency key behavior for export creation.
  - Add tests for serializer output independent from HTTP routing.
- Acceptance Criteria:
  - Adding a new export template does not require changing document review logic.
  - Export creation can be retried without creating duplicate inconsistent batches.
  - Large export behavior is documented.

#### AG-7 Remove or isolate demo store from production platform APIs
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `27 passed, 1 deselected`.
- JTBD: As a platform maintainer, I need production APIs to use persistent sources consistently.
- Description: Decide whether `app.core.store` is demo-only and prevent it from leaking into production endpoints.
- Implementation:
  - Audit endpoints using `store`.
  - Move production organization listing to repositories/services or mark endpoint demo-only.
  - Add tests/config checks so production mode does not serve mutable in-memory platform data.
- Acceptance Criteria:
  - Production platform APIs are DB-backed or explicitly disabled.
  - Demo store usage is documented and environment-gated.
  - No frontend feature depends on demo-only organization data for production flows.

#### AG-8 Define correlation ID propagation across async work
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `29 passed, 1 deselected`.
- JTBD: As an operator, I need to trace one document from upload through OCR, review and export.
- Description: Extend traceability architecture beyond HTTP request logs.
- Implementation:
  - Define correlation ID storage on background jobs and audit events if needed.
  - Propagate upload/request trace ID into OCR job payload and audit metadata safely.
  - Include correlation ID in export batch audit events.
  - Add tests or assertions for correlation continuity where practical.
- Acceptance Criteria:
  - A single document workflow can be followed across request log, background job and audit events.
  - Correlation metadata does not include sensitive payload data.
  - Background worker logs include enough identifiers for diagnosis.

## Sequential Subtask Execution Plan

Use this list as the agent execution queue. Complete subtasks in order. Do not skip verification subtasks unless the referenced command is impossible in the local environment, and record the blocker before moving on.

### Task 1 Subtasks: Audit Actual Backend And Frontend Surfaces

#### 1.1 Map backend bounded contexts
- Status: Done
- JTBD: As an implementation agent, I need to know which backend files own each architecture boundary so I do not modify the wrong module.
- Description: Inventory routers, services, repositories, models and tests for `core`, `platform`, `shared`, `accounting` and `dashboard`.
- Implementation:
  - Inspect `backend/app/api`, `backend/app/core`, `backend/app/domains/*`, `backend/app/tests`.
  - Map each documented bounded context to concrete files.
  - Note missing test coverage by domain.
- Acceptance Criteria:
  - `docs/PLAN.md` or a linked note lists backend files per bounded context.
  - Any undocumented backend capability is recorded as a plan discrepancy.
  - No source behavior changes are made.

#### 1.2 Map frontend workflow surfaces
- Status: Done
- JTBD: As an implementation agent, I need to know which frontend pages and clients exist before adding new UI flows.
- Description: Inventory pages, components, demo data and API client coverage for accounting, dashboard, AI/OCR and admin screens.
- Implementation:
  - Inspect `frontend/app/*`, `frontend/app/lib/*` and `frontend/package.json`.
  - Identify real API-backed screens versus demo-only screens.
  - Record missing routes for upload, review, export and auth callback.
- Acceptance Criteria:
  - Existing frontend routes and API helpers are listed.
  - Demo-only dependencies are called out.
  - The next implementation task can name the files it should modify.

#### 1.3 Compare API spec with actual routes
- Status: Done
- JTBD: As an implementation agent, I need the API spec to reflect real endpoints before wiring frontend calls.
- Description: Compare `docs/api-spec.md` with `backend/app/domains/*/router.py`.
- Implementation:
  - List endpoints present in code but missing in API spec.
  - List endpoints in API spec that have a different path, response shape or behavior in code.
  - Mark which mismatches block frontend work.
- Acceptance Criteria:
  - Mismatches are explicitly documented.
  - Upload, OCR job, OCR result update, approval and export endpoints are accounted for.
  - No API contract is changed in this audit subtask.

#### 1.4 Verify current baseline
- Status: Done
- Verification: Latest backend verification from `backend/`: `python3 -m compileall app` passed; `python3 -m pytest app/tests -q -m 'not integration'` passed with `29 passed, 1 deselected`. Frontend verification remains blocked until dependencies are installed.
- JTBD: As an implementation agent, I need a green or clearly blocked baseline before changing code.
- Description: Run available backend and frontend checks.
- Implementation:
  - Run `python3 -m compileall backend/app`.
  - Run `python3 -m pytest backend/app/tests -q -m 'not integration'`.
  - Run frontend `npm run build` and `npm run lint` only after dependencies are installed.
- Acceptance Criteria:
  - Backend compile result is recorded.
  - Backend test result is recorded.
  - Frontend result is either recorded as pass/fail or blocked by missing dependencies.

### Task 2 Subtasks: Implement Production Multipart Upload UI

#### 2.0 Harden backend upload safety before expanding UI usage
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `33 passed, 1 deselected`.
- JTBD: As a security reviewer, I need the upload endpoint to reject unsafe or expensive files before more users can reach it from the UI.
- Description: Strengthen server-side upload controls before building the production upload surface.
- Implementation:
  - Avoid unbounded memory reads where FastAPI/UploadFile streaming or bounded chunk reads can be used.
  - Validate server-side MIME, extension and file signature/magic bytes for PDF, PNG and JPEG.
  - Sanitize original filenames before using them in storage metadata or storage keys.
  - Add content hash calculation and document duplicate detection planning for file hash plus invoice identity fields when available.
  - Add tests for oversized file, unsupported MIME, MIME/extension mismatch and unsafe filename.
- Acceptance Criteria:
  - Upload validation happens server-side even if frontend validation is bypassed.
  - Unsafe filenames cannot influence storage path traversal or surprising object keys.
  - Oversized files are rejected without requiring the entire file to be trusted in application memory.
  - Duplicate detection approach is documented or implemented with tests for file-hash duplicate at minimum.

#### 2.1 Add multipart API client helper
- Status: Done
- Verification: `rg` confirmed `apiPostForm` and `uploadAccountingDocument`; `npm run build` remains blocked by missing frontend dependencies (`next: command not found`).
- JTBD: As an accountant, I need the UI to send real PDF/image files to the backend upload endpoint.
- Description: Add a frontend helper for `POST /accounting/documents/upload` using `FormData`.
- Implementation:
  - Add typed upload request/response helpers in `frontend/app/lib/accounting-api.ts` or a nearby API module.
  - Preserve existing `NEXT_PUBLIC_API_BASE_URL` behavior.
  - Do not manually set `Content-Type` for multipart requests.
- Acceptance Criteria:
  - Helper sends `file`, `client_company_id`, `document_type`, `category` and `accounting_period`.
  - Helper returns the backend `AccountingDocumentOut` shape.
  - Existing metadata list fetching still works.

#### 2.2 Replace metadata-only form with real upload form
- Status: Done
- Verification: `rg` confirmed `CreateDocumentForm` uses `uploadAccountingDocument` and file input; `npm run build` remains blocked by missing frontend dependencies (`next: command not found`).
- JTBD: As an accountant, I need one form that captures file and accounting metadata together.
- Description: Update `CreateDocumentForm` so it uploads a selected file instead of creating metadata-only documents.
- Implementation:
  - Add file input accepting PDF, PNG and JPG/JPEG.
  - Keep metadata controls for client company, period, document type and category.
  - Submit through the multipart helper from subtask 2.1.
- Acceptance Criteria:
  - The form no longer posts to `/accounting/documents` for the primary upload workflow.
  - Required metadata and file selection are enforced before submit.
  - Successful upload clears the form or presents a clear uploaded state.

#### 2.3 Add upload validation and user states
- Status: Done
- Verification: `rg` confirmed file type/size validation, selected file display and uploading/success/error states; `npm run build` remains blocked by missing frontend dependencies (`next: command not found`).
- JTBD: As an accountant, I need immediate feedback when a selected document cannot be uploaded.
- Description: Add client-side validation and state rendering for upload progress, success and failures.
- Implementation:
  - Validate MIME type and maximum file size using backend settings as guidance.
  - Show selected filename, size, uploading state, success state and error state.
  - Keep error messages operational and specific without exposing internals.
- Acceptance Criteria:
  - Invalid file type is blocked before network submit.
  - Oversized file is blocked before network submit.
  - Network/API failure leaves form recoverable for retry.

#### 2.4 Refresh accounting document list after upload
- Status: Done
- Verification: `rg` confirmed upload success calls `router.refresh()` and document list uses `getAccountingDocuments`; `npm run build` remains blocked by missing frontend dependencies (`next: command not found`).
- JTBD: As an accountant, I need to see the uploaded document enter the lifecycle immediately.
- Description: Update the accounting page after upload completes.
- Implementation:
  - Use NextJS refresh, local optimistic append, or a small client-side list wrapper consistent with the existing app.
  - Preserve fallback demo behavior only for unavailable backend reads.
  - Ensure uploaded status and period are visible in the table.
  - Do not fetch unbounded document lists; use the documented page size or default bounded API behavior.
- Acceptance Criteria:
  - After successful upload, the new document is visible without manually navigating away.
  - Duplicate rows are not introduced on repeated refresh.
  - Backend-created document status is displayed as returned.
  - Refresh behavior remains bounded for organizations with many documents.

#### 2.5 Verify upload workflow
- Status: Done
- Verification: `cd backend && python3 -m compileall app` passed; `cd backend && python3 -m pytest app/tests -q -m 'not integration'` passed with `33 passed, 1 deselected`; `cd frontend && npm run lint` passed; `cd frontend && npm run build` passed.
- JTBD: As an implementation agent, I need proof that upload works end to end before starting review UI.
- Description: Add or run focused verification for frontend upload and backend upload contract.
- Implementation:
  - Add frontend test if the project test setup exists; otherwise document manual browser verification.
  - Run backend non-integration tests.
  - Run frontend build/lint after dependencies are installed.
- Acceptance Criteria:
  - A PDF or image can be uploaded locally to `POST /accounting/documents/upload`.
  - The backend returns an uploaded document with tenant-scoped metadata.
  - Verification results are recorded in this plan.

### Task 3 Subtasks: Build Reviewer Queue And Field-by-Field Correction UI

#### 3.0 Add review queue API contract for pagination and filters
- Status: Done
- JTBD: As a reviewer, I need a fast queue even when an organization has thousands of documents.
- Description: Define and implement a bounded list contract before building queue UI.
- Implementation:
  - Add or document query parameters for `status`, `client_company_id`, `accounting_period`, `limit` and `offset` or cursor.
  - Ensure repository queries remain tenant-scoped and indexed by common queue filters.
  - Return a `ListResponse` shape that includes enough metadata for pagination if the shared schema supports it; otherwise document the next schema change.
  - Add tests for status filtering, tenant isolation and limit enforcement.
- Acceptance Criteria:
  - Review queue does not depend on fetching all documents and filtering only in the browser.
  - Default page size is bounded.
  - Query tests prove cross-tenant documents are never returned.
- Verification:
  - `cd backend && python3 -m pytest app/tests -q -m 'not integration'` -> 35 passed, 1 deselected.

#### 3.1 Add review queue data helpers
- Status: Done
- JTBD: As a reviewer, I need a queue of documents that require human attention.
- Description: Add frontend API helpers for listing documents, filtering `needs_review`, fetching OCR result and saving OCR field edits.
- Implementation:
  - Extend `frontend/app/lib/accounting-api.ts` with OCR result fetch, field update and approval helpers.
  - Keep response types aligned with backend schemas.
  - Add a small adapter if backend returns fields as a dictionary but UI needs field rows.
- Acceptance Criteria:
  - The UI can load documents with `status === "needs_review"`.
  - The UI can fetch an OCR result for a selected document.
  - The UI can call the field update endpoint by `result_id` and `field_id` when field IDs are available.
- Verification:
  - `cd frontend && npm run lint` -> no ESLint warnings or errors.
  - `cd frontend && npm run build` -> production build completed.

#### 3.2 Fix OCR result shape if field IDs are missing
- Status: Done
- JTBD: As a reviewer, I need to edit a specific OCR field, so the frontend must know each field ID.
- Description: Ensure OCR result payload exposes enough field metadata for correction.
- Implementation:
  - Inspect `AccountingOcrService.get_result_for_document`.
  - If needed, update `OcrResultOut` and service serialization to return field rows with `id`, `key`, `value`, `confidence` and `source`.
  - Preserve backward compatibility where practical by keeping existing `fields` dictionary or adding a new `field_items` array.
  - Exclude raw OCR provider payload from the normal frontend result payload.
- Acceptance Criteria:
  - Frontend can identify the correct `field_id` for each editable field.
  - Existing tests are updated or added for the result payload.
  - Tenant filtering remains in repository calls.
  - Payload does not expose raw prompts, raw provider output or unrelated OCR metadata.
- Verification:
  - `cd backend && python3 -m pytest app/tests -q -m 'not integration'` -> 36 passed, 1 deselected.

#### 3.3 Build review queue route and selection flow
- JTBD: As a reviewer, I need to choose the next document from a queue without scanning all documents.
- Description: Add a review-focused UI route or section under accounting.
- Implementation:
  - Create a queue view filtered to `needs_review`.
  - Add filters for client, accounting period and confidence state where available.
  - Add selected-document state and empty/loading/error states.
- Acceptance Criteria:
  - The queue only shows tenant-visible documents needing review.
  - Selecting a row loads OCR details.
  - Empty state is useful and does not look like a broken page.

#### 3.4 Build field correction editor
- JTBD: As a reviewer, I need to compare OCR values and submit corrections field by field.
- Description: Render OCR fields with confidence and editable values.
- Implementation:
  - Render field key, current value, confidence and source.
  - Allow editing one or multiple fields.
  - Save corrections via backend field update endpoint.
  - Show saved and failed states per field or per form.
- Acceptance Criteria:
  - Edited fields persist after reload.
  - Manual source is visible where backend exposes it.
  - Failed save does not discard the reviewer input.

#### 3.5 Add approve action with validation guard
- JTBD: As a reviewer, I need to approve only documents whose OCR fields are review-ready.
- Description: Add result approval UI and guard against accidental approval.
- Implementation:
  - Wire `POST /ocr-results/{result_id}/approve`.
  - Disable approve while save is pending.
  - Require required invoice fields if those rules exist; otherwise document missing rule as follow-up.
  - Enforce required-field validation in backend service, not only in the UI.
- Acceptance Criteria:
  - Approved result changes document status to `approved`.
  - Queue removes or updates approved document.
  - Approval failure is visible and recoverable.
  - Backend rejects approval when required reviewed fields are missing or invalid.

#### 3.6 Verify review workflow
- JTBD: As an implementation agent, I need to know the review loop works before export depends on it.
- Description: Verify needs-review queue, field edit and approval.
- Implementation:
  - Use seeded or uploaded data to create an OCR result.
  - Edit at least one field.
  - Approve the result.
  - Run backend and frontend checks available locally.
- Acceptance Criteria:
  - Field edit audit event is created.
  - Result/document status becomes approved.
  - Verification notes are added to the plan.

### Task 4 Subtasks: Add OCR Confidence Visualization And Review Routing

#### 4.0 Add OCR data minimization policy
- JTBD: As a security reviewer, I need OCR outputs to be useful for review without exposing raw provider data broadly.
- Description: Define what OCR data can be stored, serialized and displayed.
- Implementation:
  - Document allowed frontend fields: field ID, key, value, confidence, source and confidence level.
  - Keep raw provider payload restricted to backend diagnostics/admin-only paths if retained.
  - Add tests proving normal OCR result responses exclude raw payload.
  - Review audit events for accidental OCR text leakage.
- Acceptance Criteria:
  - Normal reviewer payloads contain only normalized fields.
  - Raw provider payload is not returned by default API responses.
  - Audit metadata does not include raw OCR text or provider prompts.

#### 4.1 Define confidence thresholds in domain code
- JTBD: As a reviewer, I need consistent confidence meanings across backend and frontend.
- Description: Introduce low, medium and high confidence thresholds in the accounting OCR domain.
- Implementation:
  - Add constants or a small policy helper in `backend/app/domains/accounting`.
  - Avoid hard-coded threshold literals scattered across services.
  - Add tests for boundary values.
- Acceptance Criteria:
  - Thresholds are defined in one backend location.
  - Boundary tests cover low, medium and high categories.
  - Frontend can consume category or replicate constants from a documented API value.

#### 4.2 Add confidence summary to OCR result/document payloads
- JTBD: As an accountant, I need document-level confidence to prioritize review work.
- Description: Persist or compute a confidence category and expose it to queue/detail views.
- Implementation:
  - Extend OCR result serialization with `confidence_level` or equivalent.
  - Consider adding document list summary if queue filtering needs it.
  - Keep raw provider payload private.
- Acceptance Criteria:
  - OCR detail payload includes numeric confidence and category.
  - Queue can show confidence without fetching raw provider payload.
  - No sensitive OCR raw payload is sent unnecessarily.

#### 4.3 Make OCR routing deterministic
- JTBD: As an operations owner, I need the system to route OCR results predictably based on confidence.
- Description: Apply the confidence policy when OCR completes.
- Implementation:
  - Route low/medium confidence to `needs_review`.
  - Decide whether high-confidence can become `reviewed` or remains `needs_review` for MVP; document the decision.
  - Add backend tests for routing behavior.
- Acceptance Criteria:
  - Routing behavior is tested with mock provider confidence values.
  - The decision is documented in code comments or this plan.
  - Existing lifecycle rules are not bypassed illegally.

#### 4.4 Add confidence UI treatment
- JTBD: As a reviewer, I need low-confidence fields to stand out immediately.
- Description: Add clear visual states for field and document confidence.
- Implementation:
  - Add badges or severity classes for low, medium and high confidence.
  - Add queue filter or sort by confidence level.
  - Keep color plus text/icon so the signal is accessible.
- Acceptance Criteria:
  - Low-confidence fields are visually distinct.
  - Confidence state is understandable without relying only on color.
  - Layout remains stable across long field values.

#### 4.5 Add dashboard confidence metric
- JTBD: As an admin, I need to know how much OCR work is risky or low-confidence.
- Description: Add low-confidence or needs-review confidence metric to dashboard aggregation if supported by current schema.
- Implementation:
  - Extend `DashboardAggregationService` with count query for confidence/status.
  - Wire frontend dashboard to real API if not already wired.
  - Keep demo fallback only when API is unavailable.
  - Use aggregate count queries, not full row loads, for dashboard cards.
- Acceptance Criteria:
  - Dashboard includes a low-confidence or needs-review confidence card.
  - Query is tenant-scoped.
  - No unbounded raw OCR payload scan is required.
  - Dashboard metrics remain fast for large document counts.

#### 4.6 Verify confidence behavior
- JTBD: As an implementation agent, I need confidence behavior verified before export/reporting relies on it.
- Description: Run tests and manual UI check for confidence categories.
- Implementation:
  - Run backend tests including confidence policy tests.
  - Run frontend verification for queue badges/filters.
  - Record results.
- Acceptance Criteria:
  - Low, medium and high categories are covered.
  - UI displays expected severity for sample data.
  - No regression in OCR completion flow.

### Task 5 Subtasks: Implement MISA And FAST Export Templates

#### 5.0 Add export query and artifact performance design
- JTBD: As an operations owner, I need exports to remain fast and predictable for large approved batches.
- Description: Remove N+1 export download assumptions and define a bounded artifact generation strategy.
- Implementation:
  - Replace per-item document fetch loops with a batched tenant-scoped query or repository method.
  - Fetch only fields required for export where practical.
  - Define maximum synchronous export size; route larger exports through background jobs if needed.
  - Add tests or query-level assertions for approved-only tenant-scoped batch loading.
- Acceptance Criteria:
  - Export download/generation does not fetch documents one by one.
  - Large export behavior is explicitly bounded or queued.
  - Tenant isolation is enforced in the batched export query.

#### 5.1 Define export template contract
- JTBD: As an accounting operator, I need to choose a target accounting system before generating export files.
- Description: Replace free-form export `format` usage with explicit template choices while preserving compatibility.
- Implementation:
  - Add an export template enum or validation layer for `json`, `misa` and `fast`.
  - Reject unsupported formats with a clear API error.
  - Update schemas and tests.
- Acceptance Criteria:
  - Unsupported export format returns a 400-style validation error.
  - Existing JSON export behavior still works if retained.
  - MISA and FAST are accepted template values.

#### 5.2 Build template serializers
- JTBD: As an accountant, I need exports with deterministic columns for MISA and FAST.
- Description: Add dedicated serializers for each target template.
- Implementation:
  - Create isolated serializer functions/classes in the accounting export module.
  - Map approved document and OCR/reviewed fields to stable column headers.
  - Keep unknown or missing fields deterministic as empty cells.
- Acceptance Criteria:
  - MISA export has tested headers and row mapping.
  - FAST export has tested headers and row mapping.
  - Serializer tests cover missing optional values.

#### 5.3 Generate downloadable export artifacts
- JTBD: As an accountant, I need a downloadable file, not just JSON metadata.
- Description: Store generated CSV or Excel-compatible artifact through existing storage abstraction or response streaming.
- Implementation:
  - Decide CSV first unless existing requirements demand XLSX.
  - Store generated file asset or return a safe download response.
  - Keep export batch metadata tied to generated artifact.
  - Prevent spreadsheet formula injection by escaping cells that begin with formula-control characters.
  - Ensure generated files are served with safe content type and disposition headers.
- Acceptance Criteria:
  - Export batch produces a concrete file artifact or stream.
  - Download endpoint returns file content or a safe expiring download reference.
  - Export file is tenant-scoped.
  - CSV/Excel output cannot execute formulas from OCR/user-controlled values.

#### 5.4 Add frontend export workflow
- JTBD: As an accountant, I need to select approved documents and export them for a target system.
- Description: Add frontend controls for selecting approved documents, choosing MISA/FAST and downloading the result.
- Implementation:
  - Add approved-document selection UI.
  - Add template selector.
  - Call export batch create and download endpoints.
  - Show success and failure states.
- Acceptance Criteria:
  - Only approved documents are selectable for export.
  - User can choose MISA or FAST.
  - User can download generated export output.

#### 5.5 Add export audit coverage
- JTBD: As an admin, I need export activity to be traceable.
- Description: Record export creation and download events.
- Implementation:
  - Keep existing `accounting.export_batch_created`.
  - Add download audit event if missing.
  - Ensure metadata does not include raw document content.
- Acceptance Criteria:
  - Export creation event is tested.
  - Export download event is tested.
  - Audit event is tenant-scoped and content-safe.

#### 5.6 Verify export workflow
- JTBD: As an implementation agent, I need proof that approved documents export correctly after review.
- Description: Verify approved-only export, MISA/FAST file generation and download.
- Implementation:
  - Run backend export tests.
  - Manually verify frontend selection and download.
  - Record generated template behavior in docs if needed.
- Acceptance Criteria:
  - Non-approved document export is rejected.
  - MISA and FAST outputs match tested headers.
  - Verification is recorded.

### Task 6 Subtasks: Harden Production Google SSO Callback And Session Flow

#### 6.0 Add production security configuration gate
- JTBD: As an operator, I need the app to fail closed when production security settings are unsafe.
- Description: Add startup/config checks for auth, CORS, JWT and environment-driven security defaults.
- Implementation:
  - Reject production startup or expose a failing health/config check when `jwt_secret_key` is still the local default.
  - Make allowed CORS origins environment-driven; keep localhost only for local mode.
  - Add security headers middleware or document equivalent reverse-proxy requirement.
  - Add tests for production config rejecting demo auth/header fallback.
- Acceptance Criteria:
  - Production-like environment cannot use default JWT secret.
  - Production CORS cannot silently allow only a hard-coded local origin or arbitrary origins.
  - Missing bearer auth fails closed when demo auth is disabled.

#### 6.1 Add auth mode safety config
- JTBD: As an operator, I need demo auth to be impossible to confuse with production auth.
- Description: Make demo header auth and Google demo verifier explicitly environment-gated.
- Implementation:
  - Inspect `settings` and `get_auth_provider`.
  - Add config that disables demo header fallback outside local/demo mode.
  - Keep local developer setup documented.
- Acceptance Criteria:
  - Production-like config rejects missing bearer token.
  - Demo config still supports documented local headers.
  - Tests cover both modes.

#### 6.2 Add Google token verifier tests
- JTBD: As a security reviewer, I need proof that invalid Google tokens are rejected.
- Description: Test demo verifier, Google verifier error handling and required claims.
- Implementation:
  - Add unit tests for invalid demo token.
  - Mock Google verifier payloads for missing subject/email and invalid token.
  - Verify error codes are stable.
- Acceptance Criteria:
  - Invalid token test passes.
  - Missing required claims test passes.
  - Demo token behavior remains explicit.

#### 6.3 Harden membership and tenant resolution
- JTBD: As a tenant admin, I need users to enter only organizations they are members of.
- Description: Ensure callback resolves organization and role from backend membership only.
- Implementation:
  - Inspect `AuthMembershipService`.
  - Add tests for user not allowed and missing active membership.
  - Ensure request headers cannot override JWT tenant after login.
- Acceptance Criteria:
  - Unknown Google profile is rejected.
  - User without membership is rejected.
  - Issued JWT contains backend-derived organization, user and role.

#### 6.4 Add frontend auth callback states
- JTBD: As a user, I need clear login feedback when Google SSO succeeds or fails.
- Description: Add frontend login/callback surface for Google ID token callback handling.
- Implementation:
  - Add callback page or component matching current NextJS app style.
  - Show loading, success, invalid token and unauthorized states.
  - Store/use returned bearer token only through the chosen session strategy.
- Acceptance Criteria:
  - Successful callback can proceed into app.
  - Failed callback shows recoverable error.
  - No token is printed or exposed in visible UI.

#### 6.5 Add SSO audit events
- JTBD: As an admin, I need login attempts to be traceable without leaking sensitive tokens.
- Description: Record successful and failed SSO attempts where appropriate.
- Implementation:
  - Add audit events after membership resolution success.
  - Add safe failed-attempt logging if user identity is available.
  - Never log raw Google ID tokens.
- Acceptance Criteria:
  - Successful SSO audit event is tested.
  - Failed SSO does not log token content.
  - Audit event includes organization only when known.

#### 6.6 Verify auth hardening
- JTBD: As an implementation agent, I need auth behavior verified before production docs are updated.
- Description: Run auth tests and local demo callback check.
- Implementation:
  - Run backend tests.
  - Verify demo mode still works with `DEMO_GOOGLE_ID_TOKEN`.
  - Verify production-like mode rejects missing/invalid auth.
- Acceptance Criteria:
  - Auth tests pass.
  - Demo mode remains documented and usable.
  - Production-like mode does not accept header-only auth unless explicitly allowed.

### Task 7 Subtasks: Add End-to-End Operational Traceability

#### 7.0 Add audit data classification rules
- JTBD: As a compliance reviewer, I need audit logs to be useful without becoming a sensitive data sink.
- Description: Define allowed and banned audit metadata fields before expanding audit UI.
- Implementation:
  - Classify safe identifiers, operational metadata and prohibited sensitive values.
  - Ban raw file contents, raw OCR text, provider prompts/responses, ID tokens, bearer tokens and export row contents from audit metadata.
  - Add helper or tests to enforce safe metadata patterns for critical events.
- Acceptance Criteria:
  - Audit metadata rules are documented in plan or code.
  - Tests cover at least OCR field update, SSO and export events for leakage.
  - Admin audit UI has a safe default rendering strategy.

#### 7.1 Standardize audit event names and payloads
- JTBD: As an admin, I need audit events to be consistent enough to search and explain.
- Description: Define canonical event names and safe metadata fields for upload, OCR, review, approval and export.
- Implementation:
  - Inventory current event names.
  - Add constants or a documented event catalog.
  - Mark sensitive fields that must never be logged.
- Acceptance Criteria:
  - Event catalog exists in code or docs.
  - Current service events align with the catalog or have migration notes.
  - Sensitive fields are explicitly excluded.

#### 7.2 Add workflow audit tests
- JTBD: As an implementation agent, I need audit behavior protected from regression.
- Description: Test audit event emission for critical accounting workflow actions.
- Implementation:
  - Add tests for upload/document creation.
  - Add tests for OCR requested/completed/failed where feasible.
  - Add tests for field update, approval, export creation and export download.
- Acceptance Criteria:
  - Each critical workflow action has at least one audit assertion.
  - Tests assert organization scoping.
  - Tests assert no raw document text/token is stored.

#### 7.3 Add export download audit event
- JTBD: As a compliance reviewer, I need to know when generated accounting exports are accessed.
- Description: Add audit logging to export download path.
- Implementation:
  - Update `download_export_batch` to accept actor user ID if needed.
  - Record `accounting.export_batch_downloaded`.
  - Keep metadata minimal.
- Acceptance Criteria:
  - Download event is recorded.
  - Event includes batch ID and format.
  - Event does not include exported row contents.

#### 7.4 Wire admin audit view to real API
- JTBD: As an admin, I need to inspect real audit events in the app, not demo cards.
- Description: Replace or supplement admin demo cards with recent audit events from `/admin/audit-events`.
- Implementation:
  - Add frontend API helper for audit event list.
  - Render recent events with action, resource, actor and timestamp.
  - Preserve loading/error states.
- Acceptance Criteria:
  - Admin page shows real tenant-scoped audit events when backend is available.
  - Demo fallback is clearly fallback behavior.
  - Sensitive metadata is not rendered by default.

#### 7.5 Add operational dashboard signals
- JTBD: As an operations owner, I need dashboard cards for OCR and export health.
- Description: Extend dashboard aggregation and frontend display beyond static demo metrics.
- Implementation:
  - Add counts for OCR queue, needs review, failed OCR and export batches.
  - Wire frontend dashboard to `/dashboard/summary`.
  - Add fallback only when backend is unavailable.
  - Use aggregate SQL queries with tenant filters and avoid loading rows into Python for counts.
- Acceptance Criteria:
  - Dashboard cards reflect backend counts.
  - Queries are tenant-scoped.
  - Failed OCR and needs-review counts are visible.
  - Dashboard remains O(number of aggregate queries), not O(number of documents).

#### 7.6 Verify traceability end to end
- JTBD: As an implementation agent, I need proof that a workflow can be explained after execution.
- Description: Run a workflow and confirm audit/dashboard visibility.
- Implementation:
  - Upload or create a document.
  - Request/execute OCR.
  - Edit a field, approve and export.
  - Inspect audit events and dashboard cards.
- Acceptance Criteria:
  - Each step has a traceable event or metric.
  - No sensitive raw content appears in audit output.
  - Verification is recorded.

### Task 8 Subtasks: Final Verification And Documentation Sync

#### 8.0 Run security and performance plan gate before final verification
- JTBD: As a reviewer, I need a final checklist proving the implementation did not skip security or performance controls.
- Description: Re-run the addendum findings as a final release gate.
- Implementation:
  - Confirm production auth fallback is closed.
  - Confirm upload validation includes size, type, signature, filename safety and duplicate strategy.
  - Confirm reviewer/OCR/export payloads exclude raw sensitive data by default.
  - Confirm queue/dashboard/export paths use bounded list, aggregate or batched queries.
  - Confirm audit events are useful and sanitized.
- Acceptance Criteria:
  - Each finding in the addendum is marked resolved, accepted risk or blocked.
  - Accepted risks include owner, reason and follow-up task.
  - No High severity finding remains unresolved before production signoff.

#### 8.1 Install or validate frontend dependencies
- JTBD: As an implementation agent, I need frontend commands to run before final signoff.
- Description: Ensure frontend dependencies are available locally.
- Implementation:
  - Run `npm install` in `frontend` if dependencies are missing and network is available.
  - If network is blocked, request approval or record blocker.
  - Do not edit lockfiles unnecessarily unless install produces one.
- Acceptance Criteria:
  - `next` is available through local `node_modules`.
  - Any dependency blocker is documented.
  - No unrelated frontend package changes are introduced.

#### 8.2 Run full backend verification
- JTBD: As a maintainer, I need backend confidence after all workflow changes.
- Description: Run compile and tests for backend.
- Implementation:
  - Run `python3 -m compileall backend/app`.
  - Run `python3 -m pytest backend/app/tests -q -m 'not integration'`.
  - Run integration tests only when database services are available.
- Acceptance Criteria:
  - Compile passes.
  - Non-integration tests pass.
  - Integration test blocker or result is recorded.

#### 8.3 Run full frontend verification
- JTBD: As a maintainer, I need frontend build health after UI changes.
- Description: Run available frontend checks.
- Implementation:
  - Run `npm run lint`.
  - Run `npm run build`.
  - Add focused manual browser checks for upload, review and export.
- Acceptance Criteria:
  - Lint passes or documented script incompatibility is resolved.
  - Build passes.
  - Manual workflow notes are recorded.

#### 8.4 Sync API documentation
- JTBD: As the next agent, I need docs to match real endpoints and payloads.
- Description: Update `docs/api-spec.md` after implementation.
- Implementation:
  - Document upload, OCR job request/execute, OCR result fetch/update/approve, export create/download and auth callback endpoints.
  - Include request/response examples that match code.
  - Remove or mark stale endpoints.
- Acceptance Criteria:
  - API spec endpoint paths match routers.
  - Required auth and tenant behavior is documented.
  - Examples include field IDs where review UI needs them.

#### 8.5 Sync architecture and README docs
- JTBD: As a new engineer, I need the architecture docs to match the implemented product.
- Description: Update architecture and README files only where behavior changed.
- Implementation:
  - Update `docs/ARCHITECTURE.md` for actual auth, OCR routing, export and observability decisions.
  - Update root/backend/frontend README run instructions if changed.
  - Avoid duplicating API spec details in architecture docs.
- Acceptance Criteria:
  - Architecture docs reflect actual module responsibilities.
  - README commands are runnable.
  - No stale claims remain about unimplemented frontend workflows.

#### 8.6 Mark final plan status
- JTBD: As the handoff recipient, I need a truthful completion record.
- Description: Update this plan with final statuses, verification results and remaining gaps.
- Implementation:
  - Mark completed task and subtask statuses.
  - Record skipped items with reason.
  - Add concise next recommended task if anything remains.
- Acceptance Criteria:
  - Every task has Done, Partial, Blocked or Not Started status.
  - Verification commands and results are listed.
  - The next agent can resume without re-auditing from scratch.

## Dependency-Ordered Task List

### Task 1: Audit Actual Backend And Frontend Surfaces

#### Summary
Create an evidence map of existing upload, OCR, review, export, auth and dashboard code before changing behavior.

#### Impact Analysis
- Affected layers: frontend pages/components, API client, FastAPI routers, services, repositories, tests.
- Affected components: accounting documents, OCR extraction, review, export batches, auth/session, dashboard metrics.
- Backward compatibility: no API or data changes; this is discovery only.

#### Implementation Steps
- [ ] List backend routers, services, models and tests that map to the documented bounded contexts.
- [ ] List frontend pages, forms and API clients that map to upload, review, export, dashboard and admin workflows.
- [ ] Compare implemented endpoints with `docs/api-spec.md` and note mismatches.
- [ ] Produce a short implementation inventory in this plan or a follow-up task note.

#### Design Decisions And Trade-offs
- Option A: start building from docs only. Faster, but risks duplicate work.
- Option B: inspect code first. Slightly slower, but prevents plan drift.
- Decision: choose Option B because the backbone is marked complete and must be verified before product-depth work.

#### Data And Query Plan
- No migrations.
- Check existing indexes and tenant filters for document list, review queue and export batch queries.

#### Security Considerations
- Confirm tenant is resolved from authenticated context for production paths.
- Flag any remaining demo headers as non-production-only.

#### Performance Considerations
- Identify any document list or dashboard query that can become N+1 under client-company scale.

#### Risks And Mitigation
- Risk: docs and code disagree.
- Mitigation: record discrepancies before implementation and update task scope rather than patching blindly.

#### Testing Strategy
- Run backend unit tests and frontend lint/build if available after inventory.
- Do not add tests in this task unless an existing test command is broken by setup drift.

#### Change Scope
- Documentation and local notes only.

#### Completeness Verdict
This task is complete when an agent can name the actual files and endpoints that implement each documented architecture component.

### Task 2: Implement Production Multipart Upload UI

#### Summary
Build the real document upload workflow in the NextJS accounting surface, wired to `POST /accounting/documents/upload`.

#### Impact Analysis
- Affected layers: frontend page/component, API client, upload form validation, backend upload contract tests if mismatches are found.
- Affected components: client company selector, document type/category/accounting period metadata, file storage boundary.
- Backward compatibility: preserve the existing upload API request and response shape from `docs/api-spec.md`.

#### Implementation Steps
- [ ] Write failing frontend test or component test for selecting a file and required metadata.
- [ ] Add file input with PDF/PNG/JPG validation, size validation and visible selected-file state.
- [ ] Add metadata controls for `client_company_id`, `document_type`, `category` and `accounting_period`.
- [ ] Submit `multipart/form-data` through the existing API base URL.
- [ ] Show uploading, success, validation error and retry states.
- [ ] Refresh or append the uploaded document in the accounting document list.
- [ ] Verify tenant/auth headers are supplied by the existing API client path.

#### Design Decisions And Trade-offs
- Option A: direct form submission inside page component. Simple, but harder to reuse and test.
- Option B: extract upload form and API call helpers. More files, but isolates validation and network behavior.
- Decision: choose Option B if the frontend already has component/API-client patterns; otherwise keep extraction minimal.

#### Data And Query Plan
- No migration expected.
- Backend should keep storing private file asset references rather than exposing raw storage paths.
- Upload response should include enough metadata to update the list without an extra full reload where practical.

#### Security Considerations
- Enforce MIME/extension checks client-side for UX and backend-side for trust.
- Do not render or log sensitive file contents.
- Ensure no organization ID can be manually supplied from the form.

#### Performance Considerations
- Avoid reading large files into frontend memory except what the browser requires for upload.
- Keep list refresh paginated or scoped if document volume is high.

#### Risks And Mitigation
- Risk: backend upload contract differs from `docs/api-spec.md`.
- Mitigation: add or update API-client adapter tests, not broad backend refactors.

#### Testing Strategy
- Frontend test for required fields, invalid file type and successful submit.
- Backend API test only if contract gaps are discovered.
- Manual verification with `npm run dev -- --port 3001` and backend running on `8001`.

#### Change Scope
- Accounting upload UI, shared API client and narrowly related tests.

#### Completeness Verdict
This is complete when a real accountant can upload a PDF/image with metadata and immediately see the document enter the platform lifecycle.

### Task 3: Build Reviewer Queue And Field-by-Field Correction UI

#### Summary
Create the review workbench for documents in `needs_review`, showing original document context beside editable OCR fields.

#### Impact Analysis
- Affected layers: frontend review page/components, accounting API client, review endpoints, audit/correction history display.
- Affected components: document list filters, OCR result schema, field correction, document status transition.
- Backward compatibility: existing review and approval APIs must remain compatible; add adapter code if response names differ.

#### Implementation Steps
- [ ] Write failing test for loading a `needs_review` queue and selecting a document.
- [ ] Add review queue filters for client, accounting period, status and confidence state.
- [ ] Render document preview using existing private asset access patterns or safe download URL.
- [ ] Render OCR fields with machine value, editable corrected value and confidence.
- [ ] Save field corrections through the review API.
- [ ] Show correction history or last-edited metadata when available.
- [ ] Add approve action that transitions reviewed documents to approved only after validation passes.

#### Design Decisions And Trade-offs
- Option A: table-only correction. Dense, but weak for PDF/image comparison.
- Option B: side-by-side preview and structured field editor. More UI work, but matches the documented human-in-the-loop workflow.
- Decision: choose Option B because architecture explicitly requires side-by-side review.

#### Data And Query Plan
- Review queue must filter by current organization and avoid cross-tenant document IDs.
- If correction history is not already queryable, add the smallest read endpoint or include it in the document review payload.
- Ensure pagination for queue lists.

#### Security Considerations
- Require accountant/admin role for review actions.
- Use expiring private asset URLs; never expose storage bucket keys directly.
- Audit every field correction and approval action.

#### Performance Considerations
- Fetch queue summaries separately from heavy document/OCR detail where possible.
- Lazy-load document previews only for the selected item.

#### Risks And Mitigation
- Risk: preview URL support is incomplete.
- Mitigation: ship queue and field editing behind the existing safe file-access contract, then add preview support as a subtask if necessary.

#### Testing Strategy
- Frontend tests for queue rendering, field edit, validation error and approve flow.
- Backend tests for RBAC, tenant isolation and correction audit persistence if missing.

#### Change Scope
- Review-focused frontend surface and minimal backend/API-client changes required for correction persistence.

#### Completeness Verdict
This is complete when a reviewer can correct low-confidence OCR fields, see what changed and approve the document with auditability.

### Task 4: Add OCR Confidence Visualization And Review Routing

#### Summary
Make confidence actionable by highlighting low-confidence fields and routing documents into review states deterministically.

#### Impact Analysis
- Affected layers: OCR service/provider normalization, document status service, frontend review UI, dashboard aggregation.
- Affected components: OCR result schema, confidence thresholds, low-confidence status, reviewer queue filters.
- Backward compatibility: preserve existing OCR result fields; add optional confidence metadata if needed.

#### Implementation Steps
- [ ] Write failing backend test for low-confidence OCR output causing `needs_review` or equivalent routing.
- [ ] Define threshold constants in the accounting OCR domain, not in UI-only code.
- [ ] Normalize field-level and document-level confidence from mock and OpenAI providers.
- [ ] Add UI severity treatment for low, medium and high confidence fields.
- [ ] Add queue filter or badge for low-confidence documents.
- [ ] Add dashboard metric for low-confidence count if dashboard aggregation already supports it.

#### Design Decisions And Trade-offs
- Option A: UI-only confidence coloring. Fast, but status behavior remains inconsistent.
- Option B: domain-level confidence routing plus UI display. Slightly more backend work, but makes workflow reliable.
- Decision: choose Option B.

#### Data And Query Plan
- Prefer existing OCR result storage if it can hold confidence metadata.
- Add indexes only if low-confidence filtering queries become table scans on persisted columns.

#### Security Considerations
- Confidence values are not secret, but document content remains private.
- Do not include OCR raw provider prompts/responses in frontend payloads unless explicitly sanitized.

#### Performance Considerations
- Compute confidence summary once during OCR completion rather than on every list render.
- Avoid loading full OCR JSON for dashboard counters.

#### Risks And Mitigation
- Risk: provider confidence output differs by model.
- Mitigation: normalize through provider adapter contracts and keep thresholds configurable.

#### Testing Strategy
- Backend tests for mock provider confidence routing.
- Frontend tests for visual states and filters.
- Regression test for high-confidence documents not being forced into review unnecessarily.

#### Change Scope
- Accounting OCR domain, status routing, review UI indicators and related tests.

#### Completeness Verdict
This is complete when low-confidence OCR is impossible to miss and consistently reaches the human review workflow.

### Task 5: Implement MISA And FAST Export Templates

#### Summary
Expand export batches into accounting-system-specific CSV/Excel templates for MISA and FAST.

#### Impact Analysis
- Affected layers: export service, serializers/templates, export API, frontend export workflow, tests.
- Affected components: approved documents, normalized invoice fields, export batch lifecycle and file asset storage.
- Backward compatibility: existing generic export behavior should continue unless superseded behind an explicit template parameter.

#### Implementation Steps
- [ ] Write failing export tests for MISA and FAST column headers and required field mapping.
- [ ] Add export template enum or equivalent typed selector.
- [ ] Map normalized OCR/reviewed fields into each template.
- [ ] Validate only approved documents can be exported.
- [ ] Store generated export file through the existing storage abstraction.
- [ ] Add frontend template selector and download action.
- [ ] Add audit log entry for export creation/download where supported.

#### Design Decisions And Trade-offs
- Option A: hard-code export columns in controller.
- Option B: isolate each template in dedicated serializer classes/functions.
- Decision: choose Option B to keep accounting-system mappings testable and extensible.

#### Data And Query Plan
- Export queries must filter by organization, client and status.
- Use projection to fetch only fields needed for export where repository patterns allow.
- No migration unless export template metadata is not currently persisted.

#### Security Considerations
- Enforce RBAC for export creation and download.
- Ensure export file URLs expire and remain tenant-scoped.
- Avoid exporting unreviewed sensitive data by accident.

#### Performance Considerations
- Batch exports should stream or generate files in background if document count is large.
- Keep initial implementation synchronous only if existing export batch workflow already bounds size safely.

#### Risks And Mitigation
- Risk: exact MISA/FAST import formats vary by customer configuration.
- Mitigation: make templates explicit, tested and easy to extend without changing OCR core.

#### Testing Strategy
- Unit tests for template mapping.
- API tests for approved-only export and tenant isolation.
- Frontend test for selecting template and receiving a download-ready batch.

#### Change Scope
- Export module, frontend export controls and narrowly related tests.

#### Completeness Verdict
This is complete when approved documents can be exported through explicit MISA/FAST templates with deterministic columns and tenant-safe downloads.

### Task 6: Harden Production Google SSO Callback And Session Flow

#### Summary
Move Google SSO from demo-friendly behavior to production-safe callback/session handling without breaking local demo mode.

#### Impact Analysis
- Affected layers: platform auth service, token verifier, session/JWT creation, frontend login/callback page, tests.
- Affected components: Google OAuth, users, organizations, memberships, RBAC and audit logs.
- Backward compatibility: preserve `GOOGLE_TOKEN_VERIFIER_MODE=demo` for local development.

#### Implementation Steps
- [ ] Write failing tests for invalid token, wrong audience, missing membership and successful login.
- [ ] Verify production mode requires `GOOGLE_CLIENT_ID` and validates issuer/audience/expiry.
- [ ] Ensure login resolves user membership and organization without trusting frontend-supplied tenant.
- [ ] Add frontend callback error states for denied, expired or unauthorized accounts.
- [ ] Add audit logs for successful and failed SSO attempts where appropriate.
- [ ] Document local demo and production env requirements.

#### Design Decisions And Trade-offs
- Option A: keep demo headers and token shortcuts broadly available.
- Option B: explicit demo mode with strict production verification.
- Decision: choose Option B because tenant isolation depends on trustworthy identity.

#### Data And Query Plan
- No migration unless membership lookup lacks required indexes.
- Membership query must be by verified user identity and organization membership, not request headers.

#### Security Considerations
- Validate JWT/session signing settings.
- Prevent open redirect in callback handling.
- Do not leak whether an email exists across organizations beyond necessary login messaging.

#### Performance Considerations
- Cache Google certs through the verifier library or existing mechanism.
- Keep membership lookup indexed by user and organization relation.

#### Risks And Mitigation
- Risk: stricter production mode breaks demo flows.
- Mitigation: keep demo mode explicit and covered by tests.

#### Testing Strategy
- Backend auth tests for token verifier modes and RBAC claims.
- Frontend callback tests for success and error states.
- Manual verification in demo mode.

#### Change Scope
- Platform auth module, frontend auth callback, env docs and tests.

#### Completeness Verdict
This is complete when production SSO cannot be spoofed by headers or malformed tokens, while local demo mode remains usable.

### Task 7: Add End-to-End Operational Traceability

#### Summary
Make upload, OCR, review, approval and export actions traceable through audit logs and dashboard-visible signals.

#### Impact Analysis
- Affected layers: core observability/audit helpers, accounting services, dashboard aggregation, admin frontend.
- Affected components: request logging, audit history, OCR job events, export events and dashboard metrics.
- Backward compatibility: additive logging and metrics only.

#### Implementation Steps
- [ ] Write failing tests for audit events on upload, OCR completion/failure, correction, approval and export.
- [ ] Standardize event names and payload shape in the appropriate core/platform helper.
- [ ] Emit audit events from accounting service boundaries, not frontend-only code.
- [ ] Add dashboard/admin view fields for recent OCR failures and export activity if existing dashboard APIs support extension.
- [ ] Ensure logs include correlation/request IDs without exposing document contents.

#### Design Decisions And Trade-offs
- Option A: ad hoc log statements in each router.
- Option B: service-level structured audit events using shared helper.
- Decision: choose Option B to keep traceability consistent and testable.

#### Data And Query Plan
- Audit queries must include organization filter.
- Add pagination for audit-history views if not already present.
- Consider indexes on organization, event type and created timestamp if audit volume is high.

#### Security Considerations
- Scrub file contents, OCR raw payloads and provider prompts from logs.
- Restrict admin audit views by RBAC.
- Preserve tenant isolation in dashboard aggregation.

#### Performance Considerations
- Keep audit writes lightweight and inside existing transaction patterns where possible.
- Avoid dashboard aggregation over unbounded audit tables.

#### Risks And Mitigation
- Risk: logging too much sensitive OCR data.
- Mitigation: define allowed audit payload fields and test against raw content leakage.

#### Testing Strategy
- Backend tests for event emission and tenant-scoped audit reads.
- Frontend/admin tests if audit events are displayed.
- Regression test for no document text in audit payloads.

#### Change Scope
- Shared observability/audit helpers, accounting service event calls, dashboard/admin display and tests.

#### Completeness Verdict
This is complete when every critical accounting workflow step is explainable after the fact without exposing sensitive document data.

### Task 8: Final Verification And Documentation Sync

#### Summary
Run the integrated verification loop and update docs so architecture, API spec and implementation plan agree.

#### Impact Analysis
- Affected layers: tests, documentation, local run instructions.
- Affected components: README, architecture, API spec, backend/frontend READMEs and this plan.
- Backward compatibility: no runtime behavior changes unless verification finds a bug that must be fixed in a preceding task.

#### Implementation Steps
- [ ] Run backend compile and non-integration tests.
- [ ] Run frontend lint/test/build commands available in `frontend/package.json`.
- [ ] Manually verify upload -> OCR/mock -> review -> approve -> export happy path.
- [ ] Update `docs/api-spec.md` for any endpoint or payload changes.
- [ ] Update `docs/ARCHITECTURE.md` only if actual architecture changed, not for implementation details.
- [ ] Mark completed tasks in this plan and record remaining known gaps.

#### Design Decisions And Trade-offs
- Option A: document after each small change.
- Option B: final doc sync after integrated verification.
- Decision: use both lightly: keep task notes current, then perform final consistency pass here.

#### Data And Query Plan
- No planned migrations.
- Verify migration state if any prior task introduced schema changes.

#### Security Considerations
- Re-check tenant isolation and RBAC tests before signing off.
- Confirm production SSO docs do not encourage unsafe demo configuration.

#### Performance Considerations
- Note any slow test, slow endpoint or export-size limitation as follow-up work.

#### Risks And Mitigation
- Risk: documentation drifts from code during multi-task execution.
- Mitigation: make this the final required task and block completion on docs consistency.

#### Testing Strategy
- Backend: `python3 -m compileall backend/app` and `python3 -m pytest backend/app/tests -q -m 'not integration'`.
- Frontend: use project scripts from `frontend/package.json`.
- Manual browser verification for the main accounting workflow.

#### Change Scope
- Verification outputs and documentation updates only, except for defects found during verification.

#### Completeness Verdict
This is complete when a new agent can read the docs, run the app and verify the accounting OCR lifecycle without discovering plan/API/architecture contradictions.
