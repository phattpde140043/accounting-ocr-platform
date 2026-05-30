from dataclasses import dataclass
from enum import StrEnum


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewRoute(StrEnum):
    AUTO_APPROVAL_CANDIDATE = "auto_approval_candidate"
    HUMAN_REVIEW = "human_review"
    EXCEPTION_QUEUE = "exception_queue"


@dataclass(frozen=True)
class ConfidenceDecision:
    level: ConfidenceLevel
    route: ReviewRoute
    reasons: tuple[str, ...]


REQUIRED_FIELDS = frozenset({"invoice_number", "total_amount"})


def classify_confidence(
    *, confidence: float, extracted_fields: dict[str, str | None]
) -> ConfidenceDecision:
    missing_fields = sorted(
        field for field in REQUIRED_FIELDS if not extracted_fields.get(field)
    )
    if missing_fields:
        return ConfidenceDecision(
            level=confidence_level(confidence),
            route=ReviewRoute.EXCEPTION_QUEUE,
            reasons=tuple(f"missing_required_field:{field}" for field in missing_fields),
        )
    if confidence < 0.70:
        return ConfidenceDecision(
            level=ConfidenceLevel.LOW,
            route=ReviewRoute.EXCEPTION_QUEUE,
            reasons=("confidence_below_0.70",),
        )
    if confidence < 0.95:
        return ConfidenceDecision(
            level=ConfidenceLevel.MEDIUM,
            route=ReviewRoute.HUMAN_REVIEW,
            reasons=("confidence_below_0.95",),
        )
    return ConfidenceDecision(
        level=ConfidenceLevel.HIGH,
        route=ReviewRoute.AUTO_APPROVAL_CANDIDATE,
        reasons=(),
    )


def confidence_level(confidence: float) -> ConfidenceLevel:
    if confidence < 0.70:
        return ConfidenceLevel.LOW
    if confidence < 0.95:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.HIGH
