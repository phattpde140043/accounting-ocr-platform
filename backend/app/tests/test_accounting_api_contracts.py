from pydantic import ValidationError

from app.domains.accounting.schemas import OcrResultOut


def test_ocr_result_contract_exposes_field_items_with_ids() -> None:
    result = OcrResultOut(
        result_id="ocrresult_1",
        document_id="doc_1",
        status="needs_review",
        confidence=0.91,
        fields={"total_amount": "1250000"},
        field_items=[
            {
                "id": "ocrfield_1",
                "key": "total_amount",
                "value": "1250000",
                "confidence": 0.86,
                "source": "ocr",
                "version": 1,
            }
        ],
    )

    assert result.field_items[0].id == "ocrfield_1"
    assert result.fields["total_amount"] == "1250000"


def test_ocr_result_contract_requires_field_item_id() -> None:
    try:
        OcrResultOut(
            document_id="doc_1",
            status="needs_review",
            confidence=0.91,
            fields={"total_amount": "1250000"},
            field_items=[
                {
                    "key": "total_amount",
                    "value": "1250000",
                    "confidence": 0.86,
                    "source": "ocr",
                }
            ],
        )
    except ValidationError as exc:
        assert "field_items.0.id" in str(exc)
    else:
        raise AssertionError("Expected missing field item ID to fail validation")


def test_ocr_result_contract_does_not_expose_raw_provider_payload() -> None:
    assert "raw_payload" not in OcrResultOut.model_fields
