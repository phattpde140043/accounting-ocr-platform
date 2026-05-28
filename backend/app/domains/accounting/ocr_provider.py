import json
from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings


@dataclass(frozen=True)
class OcrField:
    key: str
    value: str
    confidence: float


@dataclass(frozen=True)
class OcrProviderResult:
    provider: str
    fields: list[OcrField]
    raw_payload: dict
    confidence: float


@dataclass(frozen=True)
class OcrDocumentContext:
    document_id: str
    file_name: str
    mime_type: str
    file_asset_id: str | None = None
    file_data: str | None = None


class OcrProvider(Protocol):
    async def extract(self, document: OcrDocumentContext) -> OcrProviderResult:
        """Extract normalized OCR fields for a document."""


class UnknownOcrProviderError(ValueError):
    def __init__(self, provider_name: str) -> None:
        super().__init__(f"Unknown OCR provider: {provider_name}")
        self.provider_name = provider_name


class MockOcrProvider:
    provider_name = "mock"

    async def extract(self, document: OcrDocumentContext) -> OcrProviderResult:
        fields = [
            OcrField("supplier_name", "Demo Supplier", 0.92),
            OcrField("invoice_number", "INV-2026-0001", 0.9),
            OcrField("total_amount", "1250000", 0.86),
            OcrField("currency", "VND", 0.99),
        ]
        return OcrProviderResult(
            provider=self.provider_name,
            fields=fields,
            confidence=0.91,
            raw_payload={
                "document_id": document.document_id,
                "file_name": document.file_name,
                "provider": self.provider_name,
            },
        )


class OpenAiOcrProvider:
    provider_name = "openai"

    async def extract(self, document: OcrDocumentContext) -> OcrProviderResult:
        if not document.file_data:
            raise ValueError("OpenAI OCR provider requires document.file_data")

        from openai import AsyncOpenAI

        client = AsyncOpenAI()
        response = await client.responses.create(
            model=settings.openai_ocr_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Extract invoice/accounting fields from this document. "
                                "Return strict JSON with a top-level fields array. "
                                "Each field must include key, value, and confidence."
                            ),
                        },
                        self._input_payload(document),
                    ],
                }
            ],
        )
        payload = self._parse_output_text(response.output_text)
        fields = [
            OcrField(
                key=str(item.get("key", "")),
                value=str(item.get("value", "")),
                confidence=float(item.get("confidence", 0)),
            )
            for item in payload.get("fields", [])
            if item.get("key")
        ]
        confidence = max([field.confidence for field in fields], default=0)
        return OcrProviderResult(
            provider=self.provider_name,
            fields=fields,
            raw_payload=payload,
            confidence=confidence,
        )

    def _input_payload(self, document: OcrDocumentContext) -> dict:
        if document.mime_type == "application/pdf":
            return {
                "type": "input_file",
                "filename": document.file_name,
                "file_data": document.file_data,
            }
        return {
            "type": "input_image",
            "image_url": document.file_data,
            "detail": "high",
        }

    def _parse_output_text(self, output_text: str) -> dict:
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ValueError("OpenAI OCR response was not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("OpenAI OCR response must be a JSON object")
        if not isinstance(payload.get("fields", []), list):
            raise ValueError("OpenAI OCR response fields must be a list")
        return payload


OCR_PROVIDER_REGISTRY: dict[str, type[OcrProvider]] = {
    MockOcrProvider.provider_name: MockOcrProvider,
    OpenAiOcrProvider.provider_name: OpenAiOcrProvider,
}


def get_ocr_provider(provider_name: str) -> OcrProvider:
    provider_class = OCR_PROVIDER_REGISTRY.get(provider_name)
    if provider_class is None:
        raise UnknownOcrProviderError(provider_name)
    return provider_class()
