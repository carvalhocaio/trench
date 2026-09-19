from functools import lru_cache

from pydantic import Field, PositiveFloat, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


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


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()  # pyright: ignore[reportCallIssue]


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()  # pyright: ignore[reportCallIssue]


@lru_cache
def get_analytics_settings() -> AnalyticsSettings:
    return AnalyticsSettings()
