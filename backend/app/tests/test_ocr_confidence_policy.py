import pytest
from fastapi import HTTPException
from types import SimpleNamespace

from app.domains.accounting.confidence_policy import (
    ConfidenceLevel,
    ReviewRoute,
    classify_confidence,
)
from app.domains.accounting.ocr_service import AccountingOcrService


@pytest.mark.parametrize(
    ("confidence", "route", "level"),
    [
        (0.69, ReviewRoute.EXCEPTION_QUEUE, ConfidenceLevel.LOW),
        (0.70, ReviewRoute.HUMAN_REVIEW, ConfidenceLevel.MEDIUM),
        (0.9499, ReviewRoute.HUMAN_REVIEW, ConfidenceLevel.MEDIUM),
        (0.95, ReviewRoute.AUTO_APPROVAL_CANDIDATE, ConfidenceLevel.HIGH),
    ],
)
def test_confidence_policy_routes_threshold_boundaries(
    confidence: float, route: ReviewRoute, level: ConfidenceLevel
) -> None:
    decision = classify_confidence(
        confidence=confidence,
        extracted_fields={"invoice_number": "INV-1", "total_amount": "1250000"},
    )

    assert decision.route == route
    assert decision.level == level


def test_missing_required_fields_enter_exception_queue() -> None:
    decision = classify_confidence(
        confidence=0.99,
        extracted_fields={"invoice_number": "INV-1"},
    )

    assert decision.route == ReviewRoute.EXCEPTION_QUEUE
    assert decision.reasons == ("missing_required_field:total_amount",)


def test_approval_validation_rejects_missing_required_review_field() -> None:
    service = AccountingOcrService(session=None)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        service._ensure_required_review_fields(
            [SimpleNamespace(field_key="invoice_number", field_value="INV-1")]
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "required_ocr_fields_missing"
