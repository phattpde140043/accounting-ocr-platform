import pytest

from app.core.database import Base
import app.models  # noqa: F401


@pytest.mark.integration
def test_metadata_contains_core_tables() -> None:
    expected_tables = {
        "organizations",
        "users",
        "accounting_documents",
        "background_jobs",
    }
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))
