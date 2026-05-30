from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.domains.accounting.document_service import AccountingDocumentService
from app.domains.accounting.metadata_policy import validate_document_metadata
from app.domains.accounting.ocr_service import AccountingOcrService


def test_metadata_policy_accepts_supported_invoice_metadata() -> None:
    validate_document_metadata(
        document_type="invoice",
        category="sales",
        accounting_period="2026-05",
    )


@pytest.mark.parametrize(
    ("document_type", "category", "accounting_period", "error_code"),
    [
        ("unknown", "sales", "2026-05", "unsupported_document_type"),
        ("invoice", "unknown", "2026-05", "unsupported_document_category"),
        ("invoice", "sales", "2026-13", "invalid_accounting_period"),
    ],
)
def test_metadata_policy_rejects_invalid_values(
    document_type: str, category: str, accounting_period: str, error_code: str
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_document_metadata(
            document_type=document_type,
            category=category,
            accounting_period=accounting_period,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == error_code


class _ClientCompanyRepository:
    async def get_for_org(self, organization_id: str, client_company_id: str):
        return None


@pytest.mark.asyncio
async def test_metadata_rejects_cross_tenant_client_company_reference() -> None:
    service = AccountingDocumentService(session=None)  # type: ignore[arg-type]
    service.client_companies = _ClientCompanyRepository()  # type: ignore[assignment]

    with pytest.raises(HTTPException) as exc_info:
        await service._ensure_valid_metadata(
            organization_id="org_1",
            client_company_id="client_from_other_org",
            document_type="invoice",
            category="sales",
            accounting_period="2026-05",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "client_company_not_found"


class _DocumentRepository:
    def __init__(self, duplicate=None) -> None:
        self.duplicate = duplicate
        self.arguments = None

    async def get_by_invoice_identity(self, **kwargs):
        self.arguments = kwargs
        return self.duplicate


def _identity_fields() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(field_key="seller_tax_code", field_value="0312345678"),
        SimpleNamespace(field_key="invoice_number", field_value="INV-1"),
        SimpleNamespace(field_key="invoice_symbol", field_value="AA/26"),
        SimpleNamespace(field_key="invoice_date", field_value="2026-05-01"),
        SimpleNamespace(field_key="total_amount", field_value="1250000"),
    ]


@pytest.mark.asyncio
async def test_invoice_identity_is_promoted_after_review() -> None:
    repository = _DocumentRepository()
    service = AccountingOcrService(session=None)  # type: ignore[arg-type]
    service.documents = repository  # type: ignore[assignment]
    document = SimpleNamespace(id="doc_1")

    await service._promote_invoice_identity(
        organization_id="org_1",
        document=document,
        fields=_identity_fields(),  # type: ignore[arg-type]
    )

    assert document.invoice_number == "INV-1"
    assert repository.arguments["organization_id"] == "org_1"
    assert repository.arguments["exclude_document_id"] == "doc_1"


@pytest.mark.asyncio
async def test_duplicate_invoice_identity_is_rejected() -> None:
    service = AccountingOcrService(session=None)  # type: ignore[arg-type]
    service.documents = _DocumentRepository(duplicate=SimpleNamespace(id="doc_2"))  # type: ignore[assignment]

    with pytest.raises(HTTPException) as exc_info:
        await service._promote_invoice_identity(
            organization_id="org_1",
            document=SimpleNamespace(id="doc_1"),
            fields=_identity_fields(),  # type: ignore[arg-type]
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "duplicate_invoice_identity"
