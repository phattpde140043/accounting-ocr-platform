import pytest

from app.domains.accounting.ocr_provider import (
    MockOcrProvider,
    OpenAiOcrProvider,
    UnknownOcrProviderError,
    get_ocr_provider,
)


def test_registry_resolves_mock_provider() -> None:
    provider = get_ocr_provider("mock")

    assert isinstance(provider, MockOcrProvider)


def test_registry_resolves_openai_provider() -> None:
    provider = get_ocr_provider("openai")

    assert isinstance(provider, OpenAiOcrProvider)


def test_registry_rejects_unknown_provider() -> None:
    with pytest.raises(UnknownOcrProviderError) as exc_info:
        get_ocr_provider("not-a-provider")

    assert exc_info.value.provider_name == "not-a-provider"
