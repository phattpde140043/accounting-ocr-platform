from enum import StrEnum


class AccountingDocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    EXPORTED = "exported"
    FAILED = "failed"


class AccountingOcrJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AccountingOcrResultStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccountingExportBatchStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    DOWNLOADED = "downloaded"
    FAILED = "failed"


DOCUMENT_TRANSITIONS: dict[str, set[str]] = {
    AccountingDocumentStatus.UPLOADED.value: {
        AccountingDocumentStatus.QUEUED.value,
        AccountingDocumentStatus.NEEDS_REVIEW.value,
        AccountingDocumentStatus.FAILED.value,
    },
    AccountingDocumentStatus.QUEUED.value: {
        AccountingDocumentStatus.PROCESSING.value,
        AccountingDocumentStatus.FAILED.value,
    },
    AccountingDocumentStatus.PROCESSING.value: {
        AccountingDocumentStatus.NEEDS_REVIEW.value,
        AccountingDocumentStatus.FAILED.value,
    },
    AccountingDocumentStatus.NEEDS_REVIEW.value: {
        AccountingDocumentStatus.APPROVED.value,
        AccountingDocumentStatus.FAILED.value,
    },
    AccountingDocumentStatus.APPROVED.value: {
        AccountingDocumentStatus.EXPORTED.value,
    },
    AccountingDocumentStatus.EXPORTED.value: set(),
    AccountingDocumentStatus.FAILED.value: {
        AccountingDocumentStatus.QUEUED.value,
    },
}


OCR_JOB_TRANSITIONS: dict[str, set[str]] = {
    AccountingOcrJobStatus.QUEUED.value: {
        AccountingOcrJobStatus.PROCESSING.value,
        AccountingOcrJobStatus.FAILED.value,
    },
    AccountingOcrJobStatus.PROCESSING.value: {
        AccountingOcrJobStatus.COMPLETED.value,
        AccountingOcrJobStatus.FAILED.value,
    },
    AccountingOcrJobStatus.COMPLETED.value: set(),
    AccountingOcrJobStatus.FAILED.value: {
        AccountingOcrJobStatus.QUEUED.value,
    },
}


OCR_RESULT_TRANSITIONS: dict[str, set[str]] = {
    AccountingOcrResultStatus.NEEDS_REVIEW.value: {
        AccountingOcrResultStatus.APPROVED.value,
        AccountingOcrResultStatus.REJECTED.value,
    },
    AccountingOcrResultStatus.APPROVED.value: set(),
    AccountingOcrResultStatus.REJECTED.value: {
        AccountingOcrResultStatus.NEEDS_REVIEW.value,
    },
}


EXPORT_BATCH_TRANSITIONS: dict[str, set[str]] = {
    AccountingExportBatchStatus.QUEUED.value: {
        AccountingExportBatchStatus.PROCESSING.value,
        AccountingExportBatchStatus.COMPLETED.value,
        AccountingExportBatchStatus.FAILED.value,
    },
    AccountingExportBatchStatus.PROCESSING.value: {
        AccountingExportBatchStatus.COMPLETED.value,
        AccountingExportBatchStatus.FAILED.value,
    },
    AccountingExportBatchStatus.COMPLETED.value: {
        AccountingExportBatchStatus.DOWNLOADED.value,
    },
    AccountingExportBatchStatus.DOWNLOADED.value: set(),
    AccountingExportBatchStatus.FAILED.value: {
        AccountingExportBatchStatus.QUEUED.value,
    },
}


def _can_transition(
    transitions: dict[str, set[str]], current_status: str, next_status: str
) -> bool:
    return next_status in transitions.get(current_status, set())


def can_transition(current_status: str, next_status: str) -> bool:
    return can_document_transition(current_status, next_status)


def can_document_transition(current_status: str, next_status: str) -> bool:
    return _can_transition(DOCUMENT_TRANSITIONS, current_status, next_status)


def can_ocr_job_transition(current_status: str, next_status: str) -> bool:
    return _can_transition(OCR_JOB_TRANSITIONS, current_status, next_status)


def can_ocr_result_transition(current_status: str, next_status: str) -> bool:
    return _can_transition(OCR_RESULT_TRANSITIONS, current_status, next_status)


def can_export_batch_transition(current_status: str, next_status: str) -> bool:
    return _can_transition(EXPORT_BATCH_TRANSITIONS, current_status, next_status)
