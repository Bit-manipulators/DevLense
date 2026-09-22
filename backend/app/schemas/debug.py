from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

from app.analysis.complexity import ComplexityReport
from app.testing.failure_analysis import FailureEvidence

DebugMode = Literal["general", "leetcode"]
DebugStatus = Literal["fixed", "failed", "passed", "needs_review"]


class DebugRequest(BaseModel):
    mode: DebugMode = "general"
    language: str
    code: str = Field(min_length=1, max_length=50_000)
    problem_statement: str = Field(default="", max_length=20_000)
    constraints: str = Field(default="", max_length=10_000)
    error_message: str = Field(default="", max_length=20_000)
    question: str = Field(default="", max_length=4_000)
    stdin: str | None = None
    expected_output: str | None = None
    test_cases: list[dict[str, Any]] | None = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        from app.languages.registry import LanguageRegistry, UnsupportedLanguageError

        try:
            return LanguageRegistry.normalize(value)
        except UnsupportedLanguageError as exc:
            raise ValueError(str(exc)) from exc


class IterationRecord(BaseModel):
    iteration: int
    diagnosis: str
    suggested_fix: str
    diff: str
    tests_passed: int
    tests_failed: int
    validated: bool


class ValidationSummary(BaseModel):
    compile: bool
    runtime: bool
    tests: bool


class DebugReport(BaseModel):
    session_id: str | None = None
    status: DebugStatus
    language: str
    problem_summary: str
    root_cause: str
    failure_type: str
    evidence: list[FailureEvidence] = Field(default_factory=list)
    original_code: str
    corrected_code: str
    diff: str = ""
    affected_lines: list[int] = Field(default_factory=list)
    iterations: list[IterationRecord] = Field(default_factory=list)
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    validation: ValidationSummary
    complexity: ComplexityReport
