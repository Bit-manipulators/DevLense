from __future__ import annotations

import re

from app.analyzers.base import AnalysisFinding
from app.analyzers.languages.base import LanguageAnalyzer


class JavaScriptAnalyzer(LanguageAnalyzer):
    """Deterministic JavaScript diagnostics."""

    def analyze(self, code: str, error_message: str = "", question: str = "") -> AnalysisFinding:
        null_access = re.search(
            r"(?:const|let|var)\s+(?P<name>\w+)\s*=\s*(?:null|undefined)\s*;[\s\S]{0,300}?"
            r"\b(?P=name)\s*\.\s*(?P<property>\w+)",
            code,
        )
        if null_access:
            line = code[: null_access.start()].count("\n") + 1
            name = null_access.group("name")
            prop = null_access.group("property")
            return self._finding(
                summary="Null or undefined property access",
                severity="high",
                root_cause=f"`{name}` is assigned null/undefined before `{name}.{prop}` is evaluated.",
                explanation="JavaScript throws TypeError when code reads a property from null or undefined.",
                code=code,
                suggested_fix=f"Ensure `{name}` has a value or use optional chaining: `{name}?.{prop}`.",
                corrected_code=code.replace(f"{name}.{prop}", f"{name}?.{prop}", 1),
                affected_lines=[line],
                confidence=0.97,
            )

        if "ReferenceError" in error_message:
            name_match = re.search(r"(?P<name>\w+) is not defined", error_message)
            name = name_match.group("name") if name_match else "a variable"
            return self._finding(
                summary="Undefined JavaScript variable",
                severity="medium",
                root_cause=f"{name} has not been declared in the active scope.",
                explanation="JavaScript raises ReferenceError when an undeclared identifier is evaluated.",
                code=code,
                suggested_fix=f"Declare, import, or correct `{name}` before using it.",
                affected_lines=[],
                confidence=0.9,
            )

        return self._no_definite_match(code, "JavaScript")
