from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration read from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./devlens.db"
    llm_provider: str = "rule_based"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8081",
            "http://127.0.0.1:8081",
        ]
    )
    execution_timeout_seconds: int = Field(default=5, ge=1, le=30)
    max_code_size: int = Field(default=50_000, ge=1_000, le=500_000)
    max_output_size: int = Field(default=10_000, ge=1_000, le=100_000)
    max_requests_per_minute: int = Field(default=60, ge=1, le=1_000)
    execution_memory_limit_mb: int = Field(default=256, ge=64, le=2_048)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"rule_based", "ollama"}:
            return "rule_based"
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
