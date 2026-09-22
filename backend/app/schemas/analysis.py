from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SupportedLanguage = Literal["python", "cpp", "javascript", "java"]
Severity = Literal["low", "medium", "high", "critical"]

LANGUAGE_ALIASES: dict[str, SupportedLanguage] = {
    "python": "python",
    "py": "python",
    "cpp": "cpp",
    "c++": "cpp",
    "c": "cpp",
    "javascript": "javascript",
    "js": "javascript",
    "java": "java",
}


class AnalyzeRequest(BaseModel):
    language: SupportedLanguage
    code: str = Field(min_length=1, max_length=50_000)
    error_message: str = Field(default="", max_length=20_000)
    question: str = Field(default="", max_length=4_000)

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, value: Any) -> str:
        if isinstance(value, str):
            cleaned = value.strip().lower()
            if cleaned in LANGUAGE_ALIASES:
                return LANGUAGE_ALIASES[cleaned]
        return value

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Code cannot be empty.")
        return value


class AnalyzeResponse(BaseModel):
    session_id: str
    language: SupportedLanguage
    summary: str
    severity: Severity
    root_cause: str
    explanation: str
    affected_lines: list[int] = Field(default_factory=list)
    suggested_fix: str
    corrected_code: str
    debugging_steps: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
