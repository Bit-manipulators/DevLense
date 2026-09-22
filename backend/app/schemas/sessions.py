from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.analysis import Severity, SupportedLanguage


class SessionListItem(BaseModel):
    id: str
    language: SupportedLanguage
    summary: str
    severity: Severity
    confidence: float
    execution_count: int = 0
    created_at: datetime


class SessionExecutionItem(BaseModel):
    id: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    created_at: datetime


class SessionDetail(SessionListItem):
    code: str
    error_message: str
    question: str
    root_cause: str
    explanation: str
    affected_lines: list[int] = Field(default_factory=list)
    suggested_fix: str
    corrected_code: str
    debugging_steps: list[str] = Field(default_factory=list)
    mode: str = "general"
    status: str = "completed"
    diff: str = ""
    problem_statement: str = ""
    constraints: str = ""
    failure_type: str = ""
    execution_history: list[SessionExecutionItem] = Field(default_factory=list)
