from typing import Any

from pydantic_ai.models import Model, infer_model
from pydantic_ai.providers import Provider, infer_provider
from pydantic_ai.providers.google import GoogleProvider

from trench.config import LLMSettings


def build_model(settings: LLMSettings) -> Model:
    def provider_factory(name: str) -> Provider[Any]:
        if name == "google":
            return GoogleProvider(api_key=settings.api_key.get_secret_value())
        return infer_provider(name)

    return infer_model(settings.model, provider_factory=provider_factory)
