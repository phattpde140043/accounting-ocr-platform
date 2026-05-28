from app.domains.platform.audit_service import AuditEventCreate
from app.domains.platform.schemas import AuditEventOut


def test_audit_event_create_accepts_correlation_id() -> None:
    event = AuditEventCreate(
        organization_id="org_1",
        actor_user_id="user_1",
        action="accounting.ocr_requested",
        resource_type="accounting_document",
        resource_id="doc_1",
        correlation_id="corr_1",
    )

    assert event.correlation_id == "corr_1"


def test_audit_event_contract_exposes_correlation_id() -> None:
    event = AuditEventOut(
        id="audit_1",
        organization_id="org_1",
        actor_user_id="user_1",
        action="background_job.created",
        resource_type="background_job",
        resource_id="job_1",
        correlation_id="corr_1",
        metadata={},
        created_at="2026-05-28T00:00:00",
    )

    assert event.correlation_id == "corr_1"
