import re

from fastapi import HTTPException, status


DOCUMENT_TYPES = frozenset({"invoice", "receipt", "credit_note", "debit_note"})
CATEGORIES = frozenset({"sales", "purchase", "expense", "other"})
ACCOUNTING_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
INVOICE_IDENTITY_FIELDS = (
    "seller_tax_code",
    "invoice_number",
    "invoice_symbol",
    "invoice_date",
    "total_amount",
)


def validate_document_metadata(
    *, document_type: str, category: str, accounting_period: str
) -> None:
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "unsupported_document_type",
                "message": "Document type is not supported.",
            },
        )
    if category not in CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "unsupported_document_category",
                "message": "Document category is not supported.",
            },
        )
    if not ACCOUNTING_PERIOD_PATTERN.fullmatch(accounting_period):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_accounting_period",
                "message": "Accounting period must use YYYY-MM format.",
            },
        )
