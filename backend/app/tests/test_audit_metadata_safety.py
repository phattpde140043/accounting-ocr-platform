import pytest

from app.domains.platform.audit_service import validate_audit_metadata


def test_safe_audit_metadata_is_preserved() -> None:
    metadata = {"document_count": 2, "format": "misa", "nested": {"status": "done"}}

    assert validate_audit_metadata(metadata) == metadata


@pytest.mark.parametrize(
    "key",
    [
        "access_token",
        "raw_payload",
        "previous_value",
        "export_rows",
        "file_content",
        "error_message",
    ],
)
def test_sensitive_audit_metadata_keys_are_rejected(key: str) -> None:
    with pytest.raises(ValueError):
        validate_audit_metadata({key: "secret"})
