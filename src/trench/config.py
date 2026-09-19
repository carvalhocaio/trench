from collections.abc import Iterable
from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, NonNegativeFloat, PositiveFloat, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

from trench.domain.enums import AbsenceStatus, Position

Probability = Annotated[float, Field(ge=0.0, le=1.0)]

DEFAULT_POSITION_WEIGHTS: dict[Position, float] = {
    Position.QB: 6.0,
    Position.RB: 0.5,
    Position.WR: 1.0,
    Position.TE: 0.6,
    Position.OL: 0.8,
    Position.DL: 0.7,
    Position.EDGE: 1.0,
    Position.LB: 0.5,
    Position.CB: 0.8,
    Position.S: 0.5,
    Position.K: 0.6,
    Position.P: 0.2,
}

DEFAULT_ABSENCE_PROBABILITIES: dict[AbsenceStatus, float] = {
    AbsenceStatus.OUT: 1.0,
    AbsenceStatus.DOUBTFUL: 0.9,
    AbsenceStatus.QUESTIONABLE: 0.25,
}


def _require_every_member[K: StrEnum, V](
    mapping: dict[K, V], members: Iterable[K]
) -> dict[K, V]:
    missing = sorted(set(members) - mapping.keys())
    if missing:
        raise ValueError(f"missing entries for: {', '.join(missing)}")
    return mapping


class _EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)


class DatabaseSettings(_EnvSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    user: str
    password: SecretStr
    db: str
    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)

    @property
    def url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.db,
        )


class LLMSettings(_EnvSettings):
    model_config = SettingsConfigDict(env_prefix="TRENCH_LLM_")

    model: str = "google:gemini-3.8-flash"
    api_key: SecretStr = Field(validation_alias="GOOGLE_API_KEY")


class AnalyticsSettings(_EnvSettings):
    model_config = SettingsConfigDict(env_prefix="TRENCH_ANALYTICS_")

    shrinkage_games: PositiveFloat = 3.0
    home_field_advantage: float = 1.7
    score_margin_stddev: PositiveFloat = 13.5
    position_weights: dict[Position, NonNegativeFloat] = Field(
        default_factory=lambda: dict(DEFAULT_POSITION_WEIGHTS)
    )
    absence_probabilities: dict[AbsenceStatus, Probability] = Field(
        default_factory=lambda: dict(DEFAULT_ABSENCE_PROBABILITIES)
    )

    @field_validator("position_weights")
    @classmethod
    def _cover_every_position(
        cls, weights: dict[Position, float]
    ) -> dict[Position, float]:
        return _require_every_member(weights, Position)

    @field_validator("absence_probabilities")
    @classmethod
    def _cover_every_status(
        cls, probabilities: dict[AbsenceStatus, float]
    ) -> dict[AbsenceStatus, float]:
        return _require_every_member(probabilities, AbsenceStatus)


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()  # pyright: ignore[reportCallIssue]


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()  # pyright: ignore[reportCallIssue]


@lru_cache
def get_analytics_settings() -> AnalyticsSettings:
    return AnalyticsSettings()
