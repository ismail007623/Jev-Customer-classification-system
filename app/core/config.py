import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    override = os.getenv("APP_ENV", "development") == "development"
    load_dotenv(env_path, override=override)


_load_env_file()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "SupportFlow AI"
    APP_ENV: str = "development"
    OPENAI_API_KEY: str
    OPENAI_MODEL : str = "gpt-4o-mini"
    OPENROUTER_API_KEY: str | None = None
    TYPESAFE_API_KEY: str | None = None
    JEV_MODEL: str = "jev-1.13"
    CORS_ORIGINS: str = "http://localhost:3000"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    TICKET_CACHE_TTL: int = 86400  # 24 hours

    @field_validator("OPENAI_API_KEY", "TYPESAFE_API_KEY", "OPENROUTER_API_KEY", mode="before")
    @classmethod
    def strip_secret(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip().strip('"').strip("'")
        if not cleaned:
            raise ValueError("API key cannot be empty")
        return cleaned

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
