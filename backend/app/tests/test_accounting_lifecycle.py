from app.domains.accounting.lifecycle import (
    AccountingDocumentStatus,
    AccountingExportBatchStatus,
    AccountingOcrJobStatus,
    AccountingOcrResultStatus,
    can_document_transition,
    can_export_batch_transition,
    can_ocr_job_transition,
    can_ocr_result_transition,
    can_transition,
)


def test_uploaded_document_can_be_queued() -> None:
    assert can_transition(
        AccountingDocumentStatus.UPLOADED.value,
        AccountingDocumentStatus.QUEUED.value,
    )


def test_exported_document_is_terminal() -> None:
    assert not can_transition(
        AccountingDocumentStatus.EXPORTED.value,
        AccountingDocumentStatus.APPROVED.value,
    )


def test_document_review_to_approval_transition_is_allowed() -> None:
    assert can_document_transition(
        AccountingDocumentStatus.NEEDS_REVIEW.value,
        AccountingDocumentStatus.APPROVED.value,
    )


def test_document_cannot_export_before_approval() -> None:
    assert not can_document_transition(
        AccountingDocumentStatus.NEEDS_REVIEW.value,
        AccountingDocumentStatus.EXPORTED.value,
    )


def test_ocr_job_processing_to_completed_transition_is_allowed() -> None:
    assert can_ocr_job_transition(
        AccountingOcrJobStatus.PROCESSING.value,
        AccountingOcrJobStatus.COMPLETED.value,
    )


def test_completed_ocr_job_is_terminal() -> None:
    assert not can_ocr_job_transition(
        AccountingOcrJobStatus.COMPLETED.value,
        AccountingOcrJobStatus.PROCESSING.value,
    )


def test_ocr_result_needs_review_to_approved_transition_is_allowed() -> None:
    assert can_ocr_result_transition(
        AccountingOcrResultStatus.NEEDS_REVIEW.value,
        AccountingOcrResultStatus.APPROVED.value,
    )


def test_approved_ocr_result_is_terminal() -> None:
    assert not can_ocr_result_transition(
        AccountingOcrResultStatus.APPROVED.value,
        AccountingOcrResultStatus.NEEDS_REVIEW.value,
    )


def test_export_batch_queued_to_completed_transition_is_allowed_for_small_exports() -> None:
    assert can_export_batch_transition(
        AccountingExportBatchStatus.QUEUED.value,
        AccountingExportBatchStatus.COMPLETED.value,
    )


def test_downloaded_export_batch_is_terminal() -> None:
    assert not can_export_batch_transition(
        AccountingExportBatchStatus.DOWNLOADED.value,
        AccountingExportBatchStatus.COMPLETED.value,
    )
