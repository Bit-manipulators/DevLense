from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class AnalysisFinding(BaseModel):
    summary: str
    severity: str
    root_cause: str
    explanation: str
    affected_lines: list[int] = Field(default_factory=list)
    suggested_fix: str
    corrected_code: str
    debugging_steps: list[str] = Field(default_factory=list)
    confidence: float


class AnalyzerProvider(ABC):
    """Provider contract shared by local and LLM-backed analyzers."""

    @abstractmethod
    async def analyze(
        self, language: str, code: str, error_message: str = "", question: str = ""
    ) -> AnalysisFinding:
        raise NotImplementedError

