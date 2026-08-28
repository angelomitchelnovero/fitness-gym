"""Application settings loaded from environment."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- App ---
    APP_ENV: str = "development"
    APP_NAME: str = "FitnessGym"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg://gym:gym@localhost:5432/fitness_gym"

    # --- Auth ---
    # No default — must be provided via env or .env. Generate one with:
    #     python -c "import secrets; print(secrets.token_urlsafe(64))"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Mail ---
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_FROM_EMAIL: str = "no-reply@fitnessgym.example"
    SMTP_FROM_NAME: str = "FitnessGym"

    # --- Frontend ---
    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("JWT_SECRET")
    @classmethod
    def _secret_must_be_nonempty(cls, value: str) -> str:
        if not value or value.strip() == "":
            raise ValueError(
                "JWT_SECRET is required. Set it in your environment or .env file. "
                "Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        return value


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()


settings = get_settings()
