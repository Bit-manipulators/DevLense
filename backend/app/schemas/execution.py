from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.analysis import SupportedLanguage


class ExecuteRequest(BaseModel):
    language: SupportedLanguage
    code: str = Field(min_length=1, max_length=50_000)
    stdin: str = Field(default="", max_length=10_000)
    session_id: str | None = Field(default=None, max_length=36)

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Code cannot be empty.")
        return value


class ExecuteResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int = Field(ge=0)

