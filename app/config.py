from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "support systems AI"

    anthropic_api_key: SecretStr | None = None
    claude_model: str | None = None
    claude_timeout_seconds: float = Field(default=30.0, gt=0.0, lt=120.0)

    claude_max_retries: int = Field(default=2, gt=0, lt=5)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: SecretStr = SecretStr(
        "mongodb://localhost:27017",
    )

    mongodb_database: str = "supportops_ai"

@lru_cache
def get_settings() -> Settings:
    return Settings()
