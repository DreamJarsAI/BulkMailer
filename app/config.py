"""Application configuration and settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="BATCH_APP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "Email Batch Assistant"
    secret_key: str = Field(..., description="Secret used for session signing")
    fernet_key: str = Field(..., description="Key for encrypting refresh tokens")
    # Optional: when not provided, users can paste credentials in the UI
    google_client_id: str | None = Field(
        None, description="OAuth client ID for Google (optional)"
    )
    google_client_secret: str | None = Field(
        None, description="OAuth client secret for Google (optional)"
    )
    google_redirect_uri: str = Field(
        "http://localhost:8000/auth/google/callback",
        description="OAuth redirect URI",
    )
    token_storage_path: Path = Field(
        Path("data/token_store.json"),
        description="File path used to persist encrypted refresh tokens",
    )
    session_lifetime_minutes: int = Field(
        120,
        description="Minutes before ephemeral session data is purged",
    )


@lru_cache
def get_settings() -> Settings:
    """Return memoized settings instance."""

    return Settings()


__all__ = ["Settings", "get_settings"]
