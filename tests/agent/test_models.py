import pytest
from pydantic_ai.models.google import GoogleModel

from trench.agent.models import build_model
from trench.config import LLMSettings


def test_builds_gemini_model_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRENCH_LLM_MODEL", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    model = build_model(LLMSettings(_env_file=None))  # pyright: ignore[reportCallIssue]

    assert isinstance(model, GoogleModel)
    assert model.model_name == "gemini-3.8-flash"
