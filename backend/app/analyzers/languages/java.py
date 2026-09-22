from __future__ import annotations

import re

from app.analyzers.base import AnalysisFinding
from app.analyzers.languages.base import LanguageAnalyzer


class JavaAnalyzer(LanguageAnalyzer):
    """Deterministic Java diagnostics."""

    def analyze(self, code: str, error_message: str = "", question: str = "") -> AnalysisFinding:
        null_access = re.search(
            r"\b(?P<type>[A-Z]\w*)\s+(?P<name>\w+)\s*=\s*null\s*;[\s\S]{0,300}?"
            r"\b(?P=name)\s*\.",
            code,
        )
        if null_access:
            line = code[: null_access.start()].count("\n") + 1
            name = null_access.group("name")
            return self._finding(
                summary="Potential NullPointerException",
                severity="high",
                root_cause=f"`{name}` is null before a method or field is accessed.",
                explanation="Java throws NullPointerException when an instance member is accessed through null.",
                code=code,
                suggested_fix=f"Instantiate `{name}` or check `{name} != null` before accessing it.",
                corrected_code=code.replace(f"{name}.", f"if ({name} != null) {name}.", 1),
                affected_lines=[line],
                confidence=0.96,
            )

        array_loop = re.search(
            r"(?P<array>\w+)\s*=\s*new\s+\w+\s*\[\s*(?P<size>\d+)\s*\][\s\S]{0,400}?"
            r"for\s*\([^;]+;\s*(?P<index>\w+)\s*<=\s*(?P<bound>\d+)[\s\S]{0,200}?"
            r"(?P=array)\s*\[\s*(?P=index)\s*\]",
            code,
        )
        if array_loop and int(array_loop.group("bound")) >= int(array_loop.group("size")):
            line = code[: array_loop.start()].count("\n") + 1
            bound = array_loop.group("bound")
            size = array_loop.group("size")
            index = array_loop.group("index")
            return self._finding(
                summary="Potential array index out of bounds",
                severity="high",
                root_cause=f"The loop reaches index {bound}, but the array length is {size}.",
                explanation="Java arrays have valid indices from 0 to length - 1.",
                code=code,
                suggested_fix=f"Use `{index} < {size}` rather than `{index} <= {bound}`.",
                corrected_code=code.replace(f"{index} <= {bound}", f"{index} < {size}", 1),
                affected_lines=[line],
                confidence=0.95,
            )

        # General off-by-one loop condition in Java
        general_loop = re.search(
            r"for\s*\(\s*(?:int|long)\s+(?P<index>\w+)\s*=\s*0\s*;\s*"
            r"(?P=index)\s*<=\s*(?P<bound>[a-zA-Z0-9_.]+)\s*;",
            code,
        )
        if general_loop:
            index = general_loop.group("index")
            bound = general_loop.group("bound")
            line = code[: general_loop.start()].count("\n") + 1
            old = f"{index} <= {bound}"
            new = f"{index} < {bound}"
            return self._finding(
                summary="Potential array index out of bounds",
                severity="high",
                root_cause=f"The loop condition `{old}` includes `{bound}`. In 0-indexed structures of size `{bound}`, valid indices are 0 to `{bound} - 1`.",
                explanation="Java arrays and lists have valid indices from 0 to length - 1.",
                code=code,
                suggested_fix=f"Change `{old}` to `{new}`.",
                corrected_code=code.replace(old, new, 1),
                affected_lines=[line],
                confidence=0.94,
            )

        if re.search(r"/\s*0(?:\D|$)", code):
            line = self._line_of(code, r"/\s*0(?:\D|$)")
            corrected = re.sub(r"/\s*0(?:\D|$)", "/ denominator /* ensure non-zero */", code, count=1)
            return self._finding(
                summary="Division by zero",
                severity="high",
                root_cause="An expression divides by literal zero.",
                explanation="Integer division by zero throws ArithmeticException in Java.",
                code=code,
                suggested_fix="Check that the denominator is non-zero before dividing.",
                corrected_code=corrected,
                affected_lines=[line] if line else [],
                confidence=0.99,
            )

        return self._no_definite_match(code, "Java")
