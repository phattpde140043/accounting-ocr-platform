from enum import StrEnum


class DomainEvent(StrEnum):
    DOCUMENT_UPLOADED = "DocumentUploaded"
    DOCUMENT_QUEUED_FOR_OCR = "DocumentQueuedForOcr"
    OCR_COMPLETED = "OcrCompleted"
    OCR_FAILED = "OcrFailed"
    OCR_FIELD_CORRECTED = "OcrFieldCorrected"
    OCR_RESULT_APPROVED = "OcrResultApproved"
    EXPORT_BATCH_CREATED = "ExportBatchCreated"
    EXPORT_COMPLETED = "ExportCompleted"
    EXPORT_DOWNLOADED = "ExportDownloaded"
    REGION_OCR_REQUESTED = "RegionOcrRequested"
