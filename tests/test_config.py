import pytest
from pydantic import ValidationError

from trench.config import AnalyticsSettings, DatabaseSettings, LLMSettings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "GOOGLE_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_database_url_uses_asyncpg_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_USER", "trench")
    monkeypatch.setenv("POSTGRES_PASSWORD", "s3cr3t")
    monkeypatch.setenv("POSTGRES_DB", "trench")

    url = DatabaseSettings(_env_file=None).url  # pyright: ignore[reportCallIssue]

    assert url.drivername == "postgresql+asyncpg"
    assert url.render_as_string(hide_password=False) == (
        "postgresql+asyncpg://trench:s3cr3t@localhost:5432/trench"
    )


def test_database_settings_require_credentials() -> None:
    with pytest.raises(ValidationError):
        DatabaseSettings(_env_file=None)  # pyright: ignore[reportCallIssue]


def test_llm_settings_read_google_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "key")

    settings = LLMSettings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.api_key.get_secret_value() == "key"
    assert settings.model == "google:gemini-3.8-flash"


def test_analytics_settings_reject_non_positive_stddev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRENCH_ANALYTICS_SCORE_MARGIN_STDDEV", "0")

    with pytest.raises(ValidationError):
        AnalyticsSettings(_env_file=None)  # pyright: ignore[reportCallIssue]
