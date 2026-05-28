import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from typing import Protocol

from fastapi import HTTPException, status


class ExportTemplate(StrEnum):
    JSON = "json"
    MISA = "misa"
    FAST = "fast"


class ExportableDocument(Protocol):
    id: str
    client_company_id: str
    document_type: str
    category: str
    accounting_period: str
    file_name: str
    status: str
    seller_tax_code: str | None
    invoice_number: str | None
    invoice_symbol: str | None
    invoice_date: str | None
    total_amount: str | None


@dataclass(frozen=True)
class ExportArtifact:
    file_name: str
    content_type: str
    content: bytes


MISA_HEADERS = [
    "document_id",
    "client_company_id",
    "invoice_number",
    "invoice_symbol",
    "invoice_date",
    "seller_tax_code",
    "total_amount",
]

FAST_HEADERS = [
    "document_id",
    "period",
    "document_type",
    "category",
    "invoice_number",
    "seller_tax_code",
    "amount",
]


def normalize_export_template(value: str) -> ExportTemplate:
    try:
        return ExportTemplate(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "unsupported_export_template",
                "message": "Export format must be one of: json, misa, fast.",
            },
        ) from exc


def build_export_artifact(
    template: ExportTemplate, documents: list[ExportableDocument]
) -> ExportArtifact:
    if template == ExportTemplate.MISA:
        return ExportArtifact(
            file_name="misa-export.csv",
            content_type="text/csv; charset=utf-8",
            content=_build_csv(MISA_HEADERS, [_misa_row(document) for document in documents]),
        )
    if template == ExportTemplate.FAST:
        return ExportArtifact(
            file_name="fast-export.csv",
            content_type="text/csv; charset=utf-8",
            content=_build_csv(FAST_HEADERS, [_fast_row(document) for document in documents]),
        )
    return ExportArtifact(
        file_name="accounting-export.json",
        content_type="application/json",
        content=_build_json_like_payload(documents),
    )


def escape_spreadsheet_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


def _misa_row(document: ExportableDocument) -> list[str]:
    return [
        document.id,
        document.client_company_id,
        document.invoice_number or "",
        document.invoice_symbol or "",
        document.invoice_date or "",
        document.seller_tax_code or "",
        document.total_amount or "",
    ]


def _fast_row(document: ExportableDocument) -> list[str]:
    return [
        document.id,
        document.accounting_period,
        document.document_type,
        document.category,
        document.invoice_number or "",
        document.seller_tax_code or "",
        document.total_amount or "",
    ]


def _build_csv(headers: list[str], rows: list[list[object]]) -> bytes:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([escape_spreadsheet_cell(value) for value in row])
    return output.getvalue().encode("utf-8")


def _build_json_like_payload(documents: list[ExportableDocument]) -> bytes:
    import json

    payload = [
        {
            "id": document.id,
            "client_company_id": document.client_company_id,
            "document_type": document.document_type,
            "category": document.category,
            "accounting_period": document.accounting_period,
            "file_name": document.file_name,
            "status": document.status,
        }
        for document in documents
    ]
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")
