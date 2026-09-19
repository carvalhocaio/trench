import json
import os

import pytest
from pydantic import ValidationError

from trench.config import AnalyticsSettings, DatabaseSettings, LLMSettings
from trench.domain.enums import AbsenceStatus, Position

SETTINGS_ENV_PREFIXES = ("POSTGRES_", "TRENCH_", "GOOGLE_API_KEY")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith(SETTINGS_ENV_PREFIXES):
            monkeypatch.delenv(name)


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


def test_analytics_settings_cover_every_position_and_status() -> None:
    settings = AnalyticsSettings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert set(settings.position_weights) == set(Position)
    assert set(settings.absence_probabilities) == set(AbsenceStatus)


def test_analytics_settings_parse_weights_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    weights = {position.value: 1.0 for position in Position} | {"QB": 7.5}
    monkeypatch.setenv("TRENCH_ANALYTICS_POSITION_WEIGHTS", json.dumps(weights))

    settings = AnalyticsSettings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.position_weights[Position.QB] == 7.5


def test_analytics_settings_reject_partial_weights(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRENCH_ANALYTICS_POSITION_WEIGHTS", '{"QB": 7.5}')

    with pytest.raises(ValidationError, match="missing entries"):
        AnalyticsSettings(_env_file=None)  # pyright: ignore[reportCallIssue]


def test_analytics_settings_reject_probability_above_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probabilities = {"OUT": 1.0, "DOUBTFUL": 1.2, "QUESTIONABLE": 0.25}
    monkeypatch.setenv(
        "TRENCH_ANALYTICS_ABSENCE_PROBABILITIES", json.dumps(probabilities)
    )

    with pytest.raises(ValidationError):
        AnalyticsSettings(_env_file=None)  # pyright: ignore[reportCallIssue]
