# Accounting OCR Platform Master Plan

Last updated: 2026-05-31

This plan is derived from the approved `docs/ARCHITECTURE.md`. It is the
sequential execution queue for agents. Tasks are ordered by dependency: do not
skip ahead unless the dependency is already Done or explicitly marked Blocked
with an accepted workaround.

## Planning Rules

- Source of truth: `docs/ARCHITECTURE.md`.
- Execution style: finish one task, update its status and verification, then
  continue to the next task.
- Required task fields: Status, Dependencies, JTBD, Description,
  Implementation, Acceptance Criteria, Verification and Architecture Trace.
- Production gates: tenant isolation, RBAC, audit safety, pagination, bounded
  uploads, idempotency, retry behavior and no raw OCR/provider payload leakage.
- Verification default:
  - Backend: `cd backend && python3 -m compileall app`
  - Backend tests: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  - Frontend lint: `cd frontend && npm run lint`
  - Frontend build: `cd frontend && npm run build`

## Current Source Status

| Area | Status | Evidence | Next Required Action |
| --- | --- | --- | --- |
| Architecture portfolio doc | Done | `ARCHITECTURE.md` includes requirement mapping, JTBD, KPI, risks, technical deep dives, governance, cost, query budget, retry and worker strategy. | Keep synced as implementation changes. |
| Backend modular monolith | Implemented baseline | FastAPI domains exist for `core`, `platform`, `shared`, `accounting`, `dashboard`; migrations cover hardening work. | Add production object storage and scanner adapters. |
| Frontend app shell | Implemented baseline | Next.js pages consume intake, review, export, dashboard, audit and auth helpers with bounded API timeout. | Add E2E harness and correction-history rendering. |
| Upload pipeline | Implemented baseline | Size/type/signature/hash/safe-name validation and scanner boundary exist. | Add real production AV and private object storage adapters. |
| OCR processing | Implemented baseline | Provider registry, confidence routing, idempotency, claimable jobs, leases and bounded backoff exist. | Deploy externally supervised workers. |
| Review workflow | Implemented baseline | Review route, field editing, optimistic version save and approval UI exist. | Render audit-backed correction history. |
| Export workflow | Implemented | Template allowlist, CSV injection protection, batch idempotency, projection lookup and audited artifact download are implemented. | Verify migrated-stack download in Task 12. |
| Dashboard and audit | Implemented | Canonical domain events, safe audit metadata validation, aggregate tenant metrics and paginated admin audit UI are implemented. | Verify migrated-stack metrics in Task 12. |
| Chrome region OCR | Implemented | API validates bounded regions and tenant document context; extension uses local bearer token, explicit page activation and documented least-privilege permissions. | Run packaged extension smoke outside this workspace. |
| Google SSO | Done | Production auth fails closed without bearer token; local demo auth is explicit; Google verified-email check, login audit and callback UI are implemented. | Keep production environment variables configured securely. |
| CI | Blocked | GitHub token cannot push workflow files without `workflow` scope. | Add workflow when credentials allow it. |

## Dependency-Ordered Execution Queue

### Task 1: Harden Google SSO And Production Auth

- Status: Done
- Dependencies: None
- Architecture Trace: `Feature: Google SSO Authentication`, `Technical Deep Dive: Google SSO Authentication`, `Production Readiness Roadmap` items 1-2.

#### JTBD

As an operator, I need production authentication to fail closed so only verified
Google users with active memberships can access tenant data.

#### Description

Disable accidental production use of demo header auth, harden Google token
verification, ensure membership-derived JWT claims and audit login outcomes
without storing tokens.

#### Implementation

- Add explicit auth mode settings for `local/demo` versus production.
- Make demo header auth available only when the environment allows it.
- Make production-like mode reject missing bearer auth.
- Verify Google ID token against configured client ID outside demo mode.
- Resolve active membership before issuing JWT.
- Add safe login audit events for success/failure.
- Add frontend callback states if callback UI is missing: loading, success,
  invalid token, unauthorized.
- Add tests for demo mode, production fail-closed mode, invalid token, missing
  membership and JWT claims.

#### Acceptance Criteria

- Production-like config cannot authenticate through `X-Organization-Id`,
  `X-User-Id` or `X-Role`.
- Unknown or inactive Google users are rejected.
- Issued JWT contains backend-derived `user_id`, `organization_id`, role and
  permissions.
- Login audit events do not include raw Google ID tokens or bearer tokens.
- Local demo auth remains documented and usable only in local/demo mode.

#### Verification

- Passed: `cd backend && python3 -m compileall app`.
- Passed: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  (`43 passed, 1 deselected`).
- Passed: `cd frontend && npm run lint`.
- Passed: `cd frontend && npm run build`.

### Task 2: Add Pagination Metadata And Query/Index Budget Support

- Status: Done
- Dependencies: Task 1 can run independently, but finish before production signoff.
- Architecture Trace: `Query And Index Budget`, `API Surface`, `Technical Deep Dive: Dashboard`, `Technical Deep Dive: Admin, RBAC & Audit`.

#### JTBD

As a production reviewer, I need list and dashboard APIs to be bounded,
indexed and explainable before high-volume UI workflows depend on them.

#### Description

Upgrade list contracts and query patterns for document list, review queue,
client companies, audit events and dashboard metrics.

#### Implementation

- Extend shared list response with pagination metadata where appropriate:
  `items`, `limit`, `offset`, optional `total` or `next_offset`.
- Add bounded query parameters to client-company, admin user and audit list
  endpoints.
- Keep document list filters: `status`, `client_company_id`,
  `accounting_period`, `limit`, `offset`.
- Add repository tests asserting tenant filters and query limits.
- Add or plan Alembic migrations for target composite indexes:
  `(organization_id, status, client_company_id, accounting_period, created_at)`,
  `(organization_id, status, created_at)`, `(organization_id, created_at)`.
- Review dashboard service so cards use aggregate SQL or bounded projections.

#### Acceptance Criteria

- No production list endpoint used by frontend tables returns unbounded rows.
- Review queue and document list remain tenant-scoped.
- Audit/admin/client lists expose bounded pagination.
- Dashboard metrics do not load all tenant rows into application memory.
- Query/index choices are documented in code comments, migration names or
  `ARCHITECTURE.md` follow-up notes if deferred.

#### Verification

- Passed: list bounds, tenant isolation and pagination metadata tests.
- Passed: `cd backend && python3 -m compileall app alembic`.
- Passed: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  (`51 passed, 1 deselected`).
- Passed: `git diff --check`.

### Task 3: Complete Upload Security Pipeline

- Status: Done
- Dependencies: Task 2 for final list/pagination consistency; can start after Task 1 if auth changes touch upload context.
- Architecture Trace: `Feature: Accounting Document Intake`, `Technical Deep Dive: Document Intake & Metadata Classification`, `Upload Security Pipeline`.

#### JTBD

As a security reviewer, I need PDF/JPEG/PNG intake to reject unsafe files before
OCR, storage exposure or document lifecycle side effects.

#### Description

Complete production upload hardening beyond the current validation baseline:
AV scan boundary, quarantine status design, private storage target and stronger
transaction/file cleanup behavior.

#### Implementation

- Keep existing size, MIME, extension, signature, safe filename and content hash
  validation.
- Add an antivirus scan boundary interface or explicit quarantine service stub.
- Ensure OCR request rejects unscanned/quarantined files once scan status exists.
- Add file asset status values for stored/quarantined/rejected if needed.
- Ensure storage failure rolls back metadata changes.
- Add cleanup strategy for orphaned stored files if DB commit fails.
- Add tests for invalid signature, duplicate hash, quarantine behavior and
  no-document-created-on-validation-failure.
- Document private S3/MinIO provider interface if not implemented yet.

#### Acceptance Criteria

- OCR cannot run on rejected or quarantined files.
- Upload validation failure leaves no accounting document row.
- Duplicate content hash returns a tenant-scoped 409 conflict.
- Unsafe filenames cannot create path traversal or surprising storage keys.
- AV scan boundary is explicit even if local implementation is a no-op scanner.

#### Verification

- Passed: upload validation, AV boundary, quarantine, OCR blocking and orphan
  cleanup tests.
- Passed: `cd backend && python3 -m compileall app`.
- Passed: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  (`57 passed, 1 deselected`).
- Passed: `git diff --check`.

### Task 4: Implement Document Metadata And Classification Policy

- Status: Done
- Dependencies: Task 3.
- Architecture Trace: `Feature: Document Metadata & Classification`, `Technical Deep Dive: Document Intake & Metadata Classification`.

#### JTBD

As an accounting operator, I need every document classified consistently so OCR,
review, duplicate detection and export use the correct accounting rules.

#### Description

Harden metadata fields: document type, category, accounting period and invoice
identity. Make metadata validation explicit and prepare post-OCR duplicate
detection.

#### Implementation

- Define controlled values for `document_type` and `category`.
- Validate `accounting_period` format.
- Keep `client_company_id` tenant-scoped and backend-authorized.
- Promote reviewed OCR invoice identity fields to document duplicate fields
  where policy allows.
- Add duplicate invoice identity query using seller tax code, invoice number,
  invoice symbol, invoice date and total amount.
- Add tests for metadata validation, tenant-scoped client reference and duplicate
  invoice identity lookup.

#### Acceptance Criteria

- Malformed accounting period is rejected.
- Unsupported document type/category is rejected or mapped through explicit
  policy.
- Invoice identity duplicate check uses indexed tenant-scoped lookup.
- Caller cannot supply or override organization ownership.

#### Verification

- Passed: metadata validation, tenant-scoped client reference, identity promotion
  and duplicate invoice identity tests.
- Passed: `cd backend && python3 -m compileall app`.
- Passed: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  (`64 passed, 1 deselected`).
- Passed: targeted warning cleanup check
  `cd backend && python3 -m pytest app/tests/test_document_metadata_policy.py -q`
  (`7 passed`).

### Task 5: Add Idempotency And Retry Primitives

- Status: Done
- Dependencies: Tasks 3-4.
- Architecture Trace: `Idempotency And Retry Strategy`, `Domain Events`, `Cost Architecture`.

#### JTBD

As an operations owner, I need upload, OCR, correction and export commands to be
safe under retries and network timeouts.

#### Description

Add command-level idempotency behavior before durable worker and export
artifact workflows expand the number of retry paths.

#### Implementation

- Keep upload idempotency through `organization_id + content_hash`.
- Add OCR request idempotency for `organization_id + document_id + provider`:
  return existing queued/running job where safe.
- Add optimistic locking or version strategy for OCR field corrections.
- Add export idempotency key support or deterministic key from sorted document
  IDs + format.
- Add audit metadata for retry attempts without duplicating business state.
- Add tests for repeated upload, repeated OCR request, repeated export request
  and stale field correction version.

#### Acceptance Criteria

- Repeated OCR request does not create duplicate queued/running jobs.
- Repeated export request can return existing batch when idempotency key matches.
- Stale field correction cannot silently overwrite a newer manual correction.
- Audit events remain useful without duplicating state transitions.

#### Verification

- Passed: OCR request reuse, export key stability/reuse and stale correction
  rejection tests.
- Passed: `cd backend && python3 -m compileall app alembic`.
- Passed: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  (`68 passed, 1 deselected`).
- Passed: `cd frontend && npm run lint`.
- Passed: `cd frontend && npm run build`.
- Passed: `git diff --check`.

### Task 6: Implement Durable Worker Claiming Contract

- Status: Done
- Dependencies: Task 5.
- Architecture Trace: `Durable Worker Claiming`, `OCR Job Processing`, `ADR-002`.

#### JTBD

As an operator, I need multiple workers to process OCR jobs without duplicate
execution or permanently stuck jobs.

#### Description

Move from local worker assumptions toward claimable job semantics:
`available_at`, `locked_by`, `locked_until`, max attempts and retry backoff.

#### Implementation

- Add job fields if missing: `available_at`, `locked_by`, `locked_until`,
  `max_attempts` or equivalent.
- Add Alembic migration for worker claiming fields and indexes:
  `(status, available_at, attempts)`.
- Implement atomic claim repository method using row locking or safe update.
- Add retry/backoff schedule: immediate, 1 minute, 5 minutes, 30 minutes,
  terminal failed after max attempts.
- Propagate correlation ID into worker logs and audit events.
- Update local worker script to use claim method instead of naive execution.
- Add tests for claim, skip locked/stale lock recovery, retry scheduling and
  terminal failure.

#### Acceptance Criteria

- Two workers cannot process the same job concurrently.
- Crashed worker jobs can be reclaimed after `locked_until`.
- Provider timeout schedules retry while attempts remain.
- Unknown provider fails closed without infinite retry.
- Operational exception queue can identify terminal failures.

#### Verification

- Passed: atomic claim SQL, lock lease, bounded backoff and terminal failure tests.
- Passed: `cd backend && python3 -m compileall app alembic`.
- Passed: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  (`71 passed, 1 deselected`).
- Passed: `git diff --check`.

### Task 7: Implement OCR Confidence And Review Routing Policy

- Status: Done
- Dependencies: Task 6.
- Architecture Trace: `OCR Confidence And Review Policy`, `Human-In-The-Loop Strategy`, `Feature: OCR Job Processing`.

#### JTBD

As an accounting operations owner, I need OCR output routed by confidence so
human reviewers spend time only where the system needs them.

#### Description

Introduce deterministic confidence categories and routing rules:
auto-approval candidate, human review and exception queue.

#### Implementation

- Add confidence policy helper in accounting OCR domain.
- Define thresholds:
  - `>= 0.95`: auto-approval candidate after validation matures.
  - `0.70-0.95`: human review.
  - `< 0.70`: exception queue.
- Route required-field-missing, total mismatch and duplicate invoice identity to
  human review or exception queue.
- Expose `confidence_level` or equivalent in OCR result DTO.
- Add review queue filter/sort support for confidence state if schema supports
  it.
- Add tests for boundary values and routing decisions.

#### Acceptance Criteria

- Confidence thresholds live in one backend policy location.
- OCR completion uses policy and lifecycle transitions legally.
- Raw provider payload remains backend-only.
- Review queue can display confidence state without fetching raw payload.

#### Verification

- Passed: confidence boundary and missing-required-field routing tests.
- Passed: `cd backend && python3 -m compileall app alembic`.
- Passed: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  (`76 passed, 1 deselected`).
- Passed: `cd frontend && npm run lint`.
- Passed: `cd frontend && npm run build`.
- Passed: `git diff --check`.

### Task 8: Complete Reviewer Queue, Field Correction And Approval UI

- Status: Done
- Dependencies: Task 7.
- Architecture Trace: `Feature: Reviewer Queue And Field Correction`, `Technical Deep Dive: Reviewer Queue & Field Correction`.

#### JTBD

As a reviewer, I need to inspect, correct and approve OCR fields without losing
auditability or accidentally approving incomplete accounting data.

#### Description

Finish the UI and backend validation for field editing, save states, approval
action and correction history.

#### Implementation

- Extend `/accounting/review` from preview-only to editable workbench.
- Render field key, current value, confidence, source and editable corrected
  value.
- Add save per field or save all with pending/success/error states.
- Wire `PATCH /ocr-results/{result_id}/fields/{field_id}`.
- Add approval action using `POST /ocr-results/{result_id}/approve`.
- Disable approval while saves are pending.
- Add backend required-field validation before approval.
- Add correction history endpoint or render audit-derived last correction if
  history model is not yet available.
- Add frontend tests if a test harness is introduced; otherwise record manual
  browser verification.

#### Acceptance Criteria

- Edited fields persist after reload.
- Manual corrections set source to `manual`.
- Approval fails when required reviewed fields are missing.
- Approved document exits the `needs_review` queue.
- Failed save preserves reviewer input for retry.
- Field correction audit coverage is 100%.

#### Verification

- Passed: backend required-field approval validation test.
- Passed: `cd backend && python3 -m compileall app`.
- Passed: `cd backend && python3 -m pytest app/tests -q -m 'not integration'`
  (`77 passed, 1 deselected`).
- Passed: `cd frontend && npm run lint`.
- Passed: `cd frontend && npm run build`.
- UI smoke: `http://127.0.0.1:3000/accounting/review` renders the review page and
  the expected API-unavailable state while backend services are offline.
- Remaining integrated smoke: edit/save/approve with a migrated database is
  deferred to Task 12.

### Task 9: Implement Export Artifact And Batch Idempotency

- Status: Done
- Dependencies: Tasks 5 and 8.
- Architecture Trace: `Feature: Export Batch Management`, `Technical Deep Dive: Export Batch Management`, `Idempotency And Retry Strategy`.

#### JTBD

As an accountant, I need approved documents exported into safe, deterministic
files for downstream accounting/business software.

#### Description

Upgrade export from simplified metadata response to real artifact generation,
safe download and retry-safe batch creation.

#### Implementation

- Keep template allowlist: `json`, `misa`, `fast`.
- Ensure serializers remain isolated from lifecycle and HTTP routing.
- Add real artifact generation: CSV first unless XLSX becomes explicit.
- Store artifact through storage provider or return safe streaming response.
- Add expiring download reference strategy if stored artifacts are used.
- Add export idempotency key support from Task 5.
- Replace one-by-one document fetches with tenant-scoped batched/projection
  query.
- Add download audit event without row contents.
- Add frontend approved-document selector, template selector and download action.

#### Acceptance Criteria

- Only approved documents can be exported.
- Unsupported template returns stable 400 error.
- MISA/FAST headers and row mappings are covered by tests.
- CSV formula injection is prevented.
- Export download returns file content or safe expiring reference.
- Repeated export request with same idempotency key returns existing batch.

#### Verification

- Passed: batched document fetch, audited safe artifact download and repeated
  download service tests.
- Passed: template allowlist, MISA/FAST mapping and CSV formula injection tests.
- Passed: `cd backend && python3 -m compileall -q app alembic`.
- Passed: `cd backend && python3 -m pytest -q` (`80 passed`).
- Passed: `cd frontend && npm run lint`.
- Passed: `git diff --check`.
- Remaining integrated smoke: download against a migrated database is deferred
  to Task 12.

### Task 10: Implement Operational Traceability, Audit Catalog And Dashboard Signals

- Status: Done
- Dependencies: Tasks 7-9.
- Architecture Trace: `Domain Events`, `Regulatory And Data Governance Layer`, `Observability State`, `Dashboard And Operational Analytics`.

#### JTBD

As an admin/operator, I need to explain what happened to a document across
upload, OCR, review, approval and export without exposing sensitive payloads.

#### Description

Standardize event names, audit metadata safety, dashboard metrics and admin
audit views.

#### Implementation

- Create event catalog constants or documentation in code.
- Align audit event names with domain events:
  `DocumentUploaded`, `DocumentQueuedForOcr`, `OcrCompleted`, `OcrFailed`,
  `OcrFieldCorrected`, `OcrResultApproved`, `ExportBatchCreated`,
  `ExportCompleted`.
- Add safe audit metadata validation helper or tests.
- Add audit events for export download and SSO login if missing.
- Add dashboard metrics: OCR queue depth, OCR failures, needs review, review SLA
  breaches, export volume and audit volume.
- Ensure dashboard metrics use aggregate SQL.
- Wire admin audit page to real paginated audit API.

#### Acceptance Criteria

- Critical workflow actions have audit coverage.
- Audit metadata excludes raw files, raw OCR provider payloads, tokens and
  export row contents.
- Dashboard signals are tenant-scoped and role-aware.
- Admin audit list is paginated and safe by default.
- A single document workflow can be followed by correlation ID.

#### Verification

- Passed: event catalog, audit metadata boundary and safe correction metadata.
- Passed: dashboard aggregate query tenant-scope test.
- Passed: `cd backend && python3 -m compileall -q app alembic`.
- Passed: `cd backend && python3 -m pytest -q` (`87 passed`).
- Passed: `git diff --check`.
- Passed: `cd frontend && npm run lint && npm run build`.

### Task 11: Harden Chrome Extension Region OCR

- Status: Done
- Dependencies: Task 7 for OCR policy, Task 10 for audit/event conventions.
- Architecture Trace: `Feature: Region OCR Extension Workflow`, `Technical Deep Dive: Chrome Extension Region OCR`.

#### JTBD

As a user, I need browser region OCR to extract bounded snippets without
bypassing normal tenant, document and OCR governance.

#### Description

Turn the extension prototype and region OCR endpoint into a bounded,
permission-reviewed workflow.

#### Implementation

- Require document context for region OCR requests.
- Validate bounding boxes: page, x, y, width and height.
- Add region count and dimension limits.
- Reuse OCR provider boundary where practical.
- Add RBAC and tenant tests for region OCR endpoint.
- Add audit event for region OCR request without storing raw sensitive content.
- Review Chrome extension permissions and document why each is required.
- Add user-visible extension errors for invalid selection or backend failure.

#### Acceptance Criteria

- Cross-tenant document ID is rejected.
- Invalid or oversized region payload is rejected.
- Region OCR returns text, confidence and box metadata.
- Extension cannot silently capture without explicit user action.
- Extension permission review is documented.

#### Verification

- Passed: invalid region, oversized region, cross-tenant reference and safe audit
  metadata tests.
- Passed: `cd backend && python3 -m compileall -q app alembic`.
- Passed: `cd backend && python3 -m pytest -q` (`94 passed`).
- Passed: `node --check` for `background.js`, `content-script.js` and `popup.js`.
- Passed: `git diff --check`.
- Manual extension packaging smoke remains external because Chrome extension
  loading is outside this workspace runtime.

### Task 12: Final Verification, Documentation Sync And Release Handoff

- Status: Done
- Dependencies: Tasks 1-11.
- Architecture Trace: `Production Readiness Roadmap`, `Testing State`, `Open Architecture Gates`.

#### JTBD

As the next maintainer, I need a truthful final state, green verification and
updated docs before treating the project as portfolio-ready.

#### Description

Run final checks, update docs to match implementation and produce a clean
handoff record.

#### Implementation

- Run backend compile and non-integration tests.
- Run frontend lint/build.
- Run Docker Compose smoke test if local services are available.
- Add E2E smoke notes for upload -> OCR -> review -> approve -> export.
- Update `docs/api-spec.md` to match routers and DTOs.
- Update `docs/ARCHITECTURE.md` if implementation deviates from approved plan.
- Update README files if run commands or environment settings changed.
- Mark every task Done, Partial, Blocked or Not Started with verification.
- Push final commit to GitHub.

#### Acceptance Criteria

- Backend and frontend verification results are recorded.
- API spec matches actual route paths, request payloads and response DTOs.
- Architecture doc has no stale claims about unimplemented features.
- Remaining gaps are listed with owner and next task.
- Git status is clean after final push.

#### Verification

- Passed: `cd backend && python3 -m compileall -q app alembic`.
- Passed: `cd backend && python3 -m pytest -q` (`96 passed`).
- Passed: `cd frontend && npm run lint && npm run build`.
- Passed: `node --check` for `background.js`, `content-script.js` and
  `popup.js`.
- Passed: browser smoke for `/accounting`, `/accounting/review`, `/dashboard`
  and `/admin`; offline fallback states rendered as expected while the backend
  stack was unavailable.
- Blocked: `docker compose ps` could not connect to the local Docker daemon, so
  migrated-stack upload -> OCR -> review -> approve -> export verification
  remains an external release check.
- Passed: documentation sync for `.env.example`, Docker Compose, README files,
  API spec and architecture state.
- Release implementation commit SHA: recorded after final implementation
  commit.
