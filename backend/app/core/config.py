"""Application configuration loaded from environment / .env.

Secrets are never hard-coded. Values are validated at startup by Pydantic so the
app fails fast on misconfiguration rather than at request time.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core ---
    environment: Literal["development", "staging", "production"] = "development"
    secret_key: str = Field(default="dev-insecure-change-me", min_length=8)
    access_token_expire_minutes: int = 60
    api_v1_prefix: str = "/api/v1"
    project_name: str = "EngineerGPT"

    # --- Database ---
    postgres_user: str = "engineergpt"
    postgres_password: str = "engineergpt"
    postgres_db: str = "engineergpt"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- AI provider ---
    ai_provider: Literal["openai", "azure", "mock"] = "openai"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-06-01"

    # --- Uploads ---
    max_upload_size_mb: int = 50
    storage_dir: str = "./storage"

    # --- Seed admin (created idempotently on startup when both are set) ---
    admin_email: str = "admin@engineergpt.local"
    admin_password: str = ""
    admin_full_name: str = "EngineerGPT Admin"

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:3000"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @computed_field  # type: ignore[prop-decorator]
    @property
    def use_mock_ai(self) -> bool:
        """Fall back to deterministic mock when no credentials are configured."""
        if self.ai_provider == "mock":
            return True
        if self.ai_provider == "openai":
            return not self.openai_api_key
        if self.ai_provider == "azure":
            return not (self.azure_openai_api_key and self.azure_openai_endpoint)
        return True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
