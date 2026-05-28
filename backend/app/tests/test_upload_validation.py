import pytest
from fastapi import HTTPException

from app.core.storage import sanitize_filename, validate_upload


def test_validate_upload_accepts_matching_pdf_signature_and_extension() -> None:
    validate_upload(
        mime_type="application/pdf",
        size_bytes=8,
        file_name="invoice.pdf",
        content=b"%PDF-1.7",
    )


def test_validate_upload_rejects_extension_mismatch() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_upload(
            mime_type="application/pdf",
            size_bytes=8,
            file_name="invoice.png",
            content=b"%PDF-1.7",
        )

    assert exc_info.value.detail["code"] == "file_extension_mismatch"


def test_validate_upload_rejects_signature_mismatch() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_upload(
            mime_type="image/png",
            size_bytes=8,
            file_name="invoice.png",
            content=b"%PDF-1.7",
        )

    assert exc_info.value.detail["code"] == "file_signature_mismatch"


def test_sanitize_filename_removes_path_and_unsafe_characters() -> None:
    assert sanitize_filename("../bad invoice?.pdf") == "bad_invoice_.pdf"
