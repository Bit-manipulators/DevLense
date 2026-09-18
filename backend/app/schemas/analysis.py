from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

SupportedLanguage = Literal["python", "cpp", "javascript", "java"]
Severity = Literal["low", "medium", "high", "critical"]


class AnalyzeRequest(BaseModel):
    language: SupportedLanguage
    code: str = Field(min_length=1, max_length=50_000)
    error_message: str = Field(default="", max_length=20_000)
    question: str = Field(default="", max_length=4_000)

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Code cannot be empty.")
        return value


class AnalyzeResponse(BaseModel):
    session_id: str
    summary: str
    severity: Severity
    root_cause: str
    explanation: str
    affected_lines: list[int] = Field(default_factory=list)
    suggested_fix: str
    corrected_code: str
    debugging_steps: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

