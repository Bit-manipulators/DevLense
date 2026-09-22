from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.analyzers.base import AnalysisFinding


class LanguageAnalyzer(ABC):
    """Base class for language-specific static diagnostic rules."""

    @abstractmethod
    def analyze(self, code: str, error_message: str = "", question: str = "") -> AnalysisFinding:
        raise NotImplementedError

    @staticmethod
    def _line_of(code: str, pattern: str, flags: int = 0) -> int | None:
        match = re.search(pattern, code, flags)
        if not match:
            return None
        return code[: match.start()].count("\n") + 1

    @staticmethod
    def _finding(
        *,
        summary: str,
        severity: str,
        root_cause: str,
        explanation: str,
        code: str,
        suggested_fix: str,
        corrected_code: str | None = None,
        affected_lines: list[int] | None = None,
        confidence: float,
        steps: list[str] | None = None,
    ) -> AnalysisFinding:
        return AnalysisFinding(
            summary=summary,
            severity=severity,
            root_cause=root_cause,
            explanation=explanation,
            affected_lines=affected_lines or [],
            suggested_fix=suggested_fix,
            corrected_code=corrected_code if corrected_code is not None else code,
            debugging_steps=steps
            or [
                "Confirm the highlighted code path with a small reproducible input.",
                "Apply the suggested correction and run the code in the isolated sandbox.",
                "Add a regression test for the failing boundary or state.",
            ],
            confidence=confidence,
        )

    def _no_definite_match(self, code: str, language_name: str) -> AnalysisFinding:
        return self._finding(
            summary="No definite fault matched the local rules",
            severity="low",
            root_cause=(
                f"The rule-based {language_name} analyzer could not prove a common issue from the supplied code and error."
            ),
            explanation=(
                f"DevLens ran its lightweight {language_name} checks, but this is not a full compiler or "
                "semantic analyzer. Use the execution output and error message to narrow the issue."
            ),
            code=code,
            suggested_fix="Run the code and inspect the reported compiler/runtime output before changing it.",
            confidence=0.25,
            steps=[
                "Run the exact failing input in the isolated sandbox.",
                "Read the first compiler or runtime error before subsequent errors.",
                "Reduce the code to the smallest reproducible example if needed.",
            ],
        )
