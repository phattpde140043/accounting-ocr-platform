from dataclasses import dataclass

import pytest
from fastapi import HTTPException

from app.domains.accounting.export_templates import (
    ExportTemplate,
    build_export_artifact,
    escape_spreadsheet_cell,
    normalize_export_template,
)


@dataclass
class ExportDocument:
    id: str = "doc_1"
    client_company_id: str = "client_1"
    document_type: str = "invoice"
    category: str = "sales"
    accounting_period: str = "2026-05"
    file_name: str = "invoice.pdf"
    status: str = "approved"
    seller_tax_code: str | None = "0312345678"
    invoice_number: str | None = "INV-1"
    invoice_symbol: str | None = "AA/26"
    invoice_date: str | None = "2026-05-01"
    total_amount: str | None = "1250000"


def test_normalize_export_template_rejects_unknown_format() -> None:
    with pytest.raises(HTTPException) as exc_info:
        normalize_export_template("xlsx-but-not-defined")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "unsupported_export_template"


def test_build_misa_export_artifact_has_stable_headers() -> None:
    artifact = build_export_artifact(ExportTemplate.MISA, [ExportDocument()])
    content = artifact.content.decode("utf-8")

    assert artifact.file_name == "misa-export.csv"
    assert content.splitlines()[0].startswith("document_id,client_company_id")
    assert "INV-1" in content


def test_build_fast_export_artifact_has_stable_headers() -> None:
    artifact = build_export_artifact(ExportTemplate.FAST, [ExportDocument()])
    content = artifact.content.decode("utf-8")

    assert artifact.file_name == "fast-export.csv"
    assert content.splitlines()[0].startswith("document_id,period")
    assert "sales" in content


def test_export_cells_escape_formula_injection_values() -> None:
    assert escape_spreadsheet_cell("=SUM(A1:A2)") == "'=SUM(A1:A2)"
    assert escape_spreadsheet_cell("+cmd") == "'+cmd"
    assert escape_spreadsheet_cell("safe") == "safe"
