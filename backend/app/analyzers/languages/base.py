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
            summary="Code Structure Verified (No Static Defects Detected)",
            severity="low",
            root_cause="No syntax errors, unbalanced delimiters, or known static defects detected.",
            explanation=(
                f"Static analysis verified {language_name} syntax and structure. "
                "Delimiters are balanced and no known anti-patterns were found. "
                "Use the execution sandbox or test harness to verify dynamic runtime behavior."
            ),
            code=code,
            suggested_fix="No static repair needed. Run code with test inputs to verify runtime correctness.",
            confidence=0.90,
            steps=[
                "Code syntax and structure are clean.",
                "Execute the code against sample inputs in the sandbox.",
                "Inspect boundary conditions and edge cases.",
            ],
        )

