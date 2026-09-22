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

        # 1. Array.prototype.last missing empty array check
        if "Array.prototype.last" in code or "prototype.last" in code:
            if "length" in code and ("-1" not in code and "=== 0" not in code and "== 0" not in code and "!this.length" not in code):
                line = self._line_of(code, r"Array\.prototype\.last|prototype\.last") or 1
                corrected = re.sub(
                    r"Array\.prototype\.last\s*=\s*function\s*\(\s*\)\s*\{[\s\S]*?\};?",
                    "Array.prototype.last = function() {\n    if (this.length === 0) return -1;\n    return this[this.length - 1];\n};",
                    code,
                )
                if corrected == code:
                    corrected = (
                        "Array.prototype.last = function() {\n"
                        "    if (this.length === 0) return -1;\n"
                        "    return this[this.length - 1];\n"
                        "};"
                    )
                return self._finding(
                    summary="Unhandled Empty Array in Array.prototype.last",
                    severity="high",
                    root_cause="Array.prototype.last returns `undefined` for empty arrays instead of `-1`.",
                    explanation=(
                        "When called on an empty array `[]`, `this.length - 1` evaluates to `-1`, resulting in `this[-1]` which is `undefined`. "
                        "The specification requires returning `-1` when the array contains no elements."
                    ),
                    code=code,
                    suggested_fix="Check if `this.length === 0` and return `-1`, otherwise return `this[this.length - 1]`.",
                    corrected_code=corrected,
                    affected_lines=[line],
                    confidence=0.96,
                    steps=[
                        "Guard for empty arrays: `if (this.length === 0) return -1;`.",
                        "Access the last index with `this[this.length - 1]` for non-empty arrays.",
                        "Verify with both empty `[]` and non-empty `[1, 2, 3]` arrays.",
                    ],
                )

        # 2. General off-by-one loop condition (for (let i = 0; i <= n; i++) or for (var i = 0; i <= arr.length; i++))
        general_loop = re.search(
            r"for\s*\(\s*(?:let|var|const)?\s*(?P<index>\w+)\s*=\s*0\s*;\s*"
            r"(?P=index)\s*<=\s*(?P<bound>[a-zA-Z0-9_.]+)\s*;",
            code,
        )
        if general_loop:
            index = general_loop.group("index")
            bound = general_loop.group("bound")
            loop_line = code[: general_loop.start()].count("\n") + 1
            old = f"{index} <= {bound}"
            new = f"{index} < {bound}"
            return self._finding(
                summary="Off-by-one loop boundary (possible undefined index or out of bounds)",
                severity="high",
                root_cause=f"The loop condition `{old}` allows index equal to `{bound}`. In 0-indexed sequences of length `{bound}`, valid indices are 0 to `{bound} - 1`.",
                explanation=(
                    f"In JavaScript, arrays and strings are 0-indexed. Iterating with `{old}` accesses index `{bound}`, "
                    "which produces `undefined` or causes unintended extra loop iterations."
                ),
                code=code,
                suggested_fix=f"Replace `{old}` with `{new}`.",
                corrected_code=code.replace(old, new, 1),
                affected_lines=[loop_line],
                confidence=0.95,
                steps=[
                    f"Change `{old}` to `{new}`.",
                    "Ensure 0-indexed iteration terminates strictly before sequence length.",
                    "Verify with edge cases in the execution sandbox.",
                ],
            )

        # 3. Invalid NaN comparison (x === NaN is always false)
        nan_check = re.search(r"(?P<expr>\w+)\s*===?\s*NaN", code)
        if nan_check:
            line = self._line_of(code, r"===?\s*NaN") or 1
            expr = nan_check.group("expr")
            corrected = re.sub(rf"{expr}\s*===?\s*NaN", f"Number.isNaN({expr})", code, count=1)
            return self._finding(
                summary="Invalid NaN comparison",
                severity="medium",
                root_cause=f"`{expr} === NaN` is always false in JavaScript because `NaN !== NaN`.",
                explanation="In JavaScript, `NaN` is not equal to anything, including `NaN`. Use `Number.isNaN()` instead.",
                code=code,
                suggested_fix=f"Replace `{nan_check.group(0)}` with `Number.isNaN({expr})`.",
                corrected_code=corrected,
                affected_lines=[line],
                confidence=0.98,
            )

        # 4. Runtime error message diagnostics
        if "TypeError" in error_message:
            return self._finding(
                summary="JavaScript TypeError",
                severity="high",
                root_cause=error_message.strip(),
                explanation=(
                    "A JavaScript TypeError occurs when an operation is performed on a value of an unexpected type, "
                    "such as calling a non-function or reading properties of `null` or `undefined`."
                ),
                code=code,
                suggested_fix="Validate operand types and use optional chaining (`?.`) or null checks before property access.",
                affected_lines=[],
                confidence=0.92,
            )

        if "SyntaxError" in error_message:
            line_m = re.search(r":(\d+)", error_message)
            line_no = int(line_m.group(1)) if line_m else 1
            return self._finding(
                summary="JavaScript SyntaxError",
                severity="critical",
                root_cause=error_message.strip(),
                explanation="JavaScript engine failed to parse the source code due to a syntax violation.",
                code=code,
                suggested_fix="Inspect delimiter matching (braces, brackets, parentheses) and token syntax.",
                affected_lines=[line_no] if line_no else [],
                confidence=0.95,
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
