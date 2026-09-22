from __future__ import annotations

import ast
import re

from app.analyzers.base import AnalysisFinding
from app.analyzers.languages.base import LanguageAnalyzer


class PythonAnalyzer(LanguageAnalyzer):
    """Deterministic Python diagnostics with intelligent syntax repair."""

    def analyze(self, code: str, error_message: str = "", question: str = "") -> AnalysisFinding:
        try:
            ast.parse(code)
        except (SyntaxError, IndentationError) as exc:
            line = exc.lineno or 1
            is_indent = isinstance(exc, IndentationError)
            corrected, specific_fix = self._attempt_syntax_fix(code, exc)
            return self._finding(
                summary="Python indentation error" if is_indent else "Python syntax error",
                severity="high",
                root_cause=exc.msg,
                explanation=(
                    "Python uses indentation as syntax, so inconsistent whitespace prevents parsing."
                    if is_indent
                    else "Python cannot parse this statement as written."
                ),
                code=code,
                suggested_fix=specific_fix,
                corrected_code=corrected,
                affected_lines=[line],
                confidence=0.98,
                steps=[
                    "Inspect the line indicated by Python.",
                    "Check the preceding line for an unclosed bracket, quote, or colon.",
                    "Use spaces consistently for indentation, then rerun the code.",
                ],
            )

        division_line = self._line_of(code, r"/\s*0(?:\D|$)")
        if division_line:
            corrected = re.sub(r"/\s*0(?:\D|$)", "/ denominator  # ensure denominator is non-zero\n", code, count=1)
            return self._finding(
                summary="Division by zero",
                severity="high",
                root_cause="A numeric expression divides by the literal value 0.",
                explanation="Division by zero raises ZeroDivisionError in Python.",
                code=code,
                suggested_fix="Validate the denominator before division; it must not be zero.",
                corrected_code=corrected,
                affected_lines=[division_line],
                confidence=0.99,
            )

        indexed_loop = re.search(
            r"(?P<array>\w+)\s*=\s*\[(?P<values>[^\]]*)\][\s\S]{0,300}?"
            r"for\s+(?P<index>\w+)\s+in\s+range\((?P<limit>\d+)\)\s*:\s*\n\s*"
            r"(?:print\()?\s*(?P=array)\s*\[\s*(?P=index)\s*\]",
            code,
        )
        if indexed_loop:
            values = [item for item in indexed_loop.group("values").split(",") if item.strip()]
            limit = int(indexed_loop.group("limit"))
            if limit > len(values):
                line = code[: indexed_loop.start()].count("\n") + 1
                corrected = re.sub(
                    rf"range\({limit}\)", f"range(len({indexed_loop.group('array')}))", code, count=1
                )
                return self._finding(
                    summary="Likely list index out of range",
                    severity="high",
                    root_cause=(
                        f"The loop runs {limit} times, but {indexed_loop.group('array')} has only {len(values)} items."
                    ),
                    explanation=(
                        "Python lists are indexed from 0 through length - 1. The final iteration accesses an "
                        "index that does not exist."
                    ),
                    code=code,
                    suggested_fix=f"Iterate with range(len({indexed_loop.group('array')})) instead of a hard-coded limit.",
                    corrected_code=corrected,
                    affected_lines=[line],
                    confidence=0.94,
                )

        # General off-by-one: range(len(arr) + 1)
        off_by_one_range = re.search(r"range\(len\((?P<arr>\w+)\)\s*\+\s*1\)", code)
        if off_by_one_range:
            line = self._line_of(code, r"range\(len\(\w+\)\s*\+\s*1\)") or 1
            arr = off_by_one_range.group("arr")
            corrected = re.sub(rf"range\(len\({arr}\)\s*\+\s*1\)", f"range(len({arr}))", code, count=1)
            return self._finding(
                summary="Likely list index out of range (off-by-one)",
                severity="high",
                root_cause=f"`range(len({arr}) + 1)` iterates up to `len({arr})`, but valid indices are 0 to `len({arr}) - 1`.",
                explanation="Python lists are 0-indexed. Accessing `arr[len(arr)]` raises `IndexError: list index out of range`.",
                code=code,
                suggested_fix=f"Use `range(len({arr}))` instead of `range(len({arr}) + 1)`.",
                corrected_code=corrected,
                affected_lines=[line],
                confidence=0.96,
            )

        # Dangerous mutable default argument
        mutable_default = re.search(r"def\s+\w+\s*\([^)]*?(?P<arg>\w+)\s*=\s*(?P<default>\[\]|\{\})", code)
        if mutable_default:
            line = self._line_of(code, r"def\s+\w+\s*\([^)]*?=\s*(\[\]|\{\})") or 1
            arg = mutable_default.group("arg")
            return self._finding(
                summary="Dangerous mutable default argument",
                severity="medium",
                root_cause=f"Default argument `{arg}` is initialized with a mutable container (`{mutable_default.group('default')}`).",
                explanation="In Python, default arguments are evaluated once at function definition time. Subsequent calls share the same mutable object.",
                code=code,
                suggested_fix=f"Set default to `None` (e.g. `{arg}=None`) and initialize inside function: `if {arg} is None: {arg} = []`.",
                affected_lines=[line],
                confidence=0.93,
            )

        if "NameError" in error_message:
            match = re.search(r"name ['\"](?P<name>\w+)['\"] is not defined", error_message)
            name = match.group("name") if match else "a referenced name"
            line = self._line_of(code, rf"\b{name}\b")
            return self._finding(
                summary="Undefined Python name",
                severity="medium",
                root_cause=f"{name} is used before it is defined or imported.",
                explanation="Python resolves names at runtime; a misspelling or missing import raises NameError.",
                code=code,
                suggested_fix=f"Define, import, or correct {name} before it is used.",
                affected_lines=[line] if line else [],
                confidence=0.92,
            )

        if "IndexError" in error_message:
            line = self._line_of(code, r"\w+\s*\[.+\]")
            return self._finding(
                summary="List index out of range",
                severity="high",
                root_cause="The supplied runtime error reports an index beyond a sequence boundary.",
                explanation="A sequence index must be between 0 and its length minus one.",
                code=code,
                suggested_fix="Check the sequence length before indexing and adjust the loop bound.",
                affected_lines=[line] if line else [],
                confidence=0.9,
            )

        if "TypeError" in error_message:
            return self._finding(
                summary="Python TypeError",
                severity="high",
                root_cause=error_message.strip(),
                explanation="Python raised a TypeError when an operation was applied to an object of inappropriate type.",
                code=code,
                suggested_fix="Verify object types before operations, or convert types explicitly.",
                affected_lines=[],
                confidence=0.91,
            )

        if "KeyError" in error_message:
            m = re.search(r"KeyError:\s*(.+)", error_message)
            key = m.group(1).strip() if m else "a key"
            return self._finding(
                summary="Dictionary KeyError",
                severity="high",
                root_cause=f"Key {key} was not found in the dictionary.",
                explanation="Accessing a non-existent dictionary key directly raises KeyError. Use `.get(key, default)` or verify with `in`.",
                code=code,
                suggested_fix=f"Use `dict.get({key})` or check `if {key} in dict:` before access.",
                affected_lines=[],
                confidence=0.92,
            )

        if "ZeroDivisionError" in error_message:
            line = self._line_of(code, r"/")
            return self._finding(
                summary="Division by zero",
                severity="high",
                root_cause="A numeric division or modulo operation evaluated with a denominator of zero.",
                explanation="Division by zero is undefined and raises ZeroDivisionError in Python.",
                code=code,
                suggested_fix="Guard denominator against zero: `if denominator != 0:`.",
                affected_lines=[line] if line else [],
                confidence=0.95,
            )

        return self._no_definite_match(code, "Python")

    @staticmethod
    def _attempt_syntax_fix(code: str, exc: SyntaxError | IndentationError) -> tuple[str, str]:
        """Attempts to deterministically correct common Python syntax and delimiter errors."""
        lines = code.splitlines()
        line_no = getattr(exc, "lineno", 1) or 1
        if not (1 <= line_no <= len(lines)):
            return code, "Correct the syntax at the highlighted line."

        target_idx = line_no - 1
        line = lines[target_idx]
        msg = str(getattr(exc, "msg", "")).lower()

        # 1. Unterminated string literal (e.g., print("Aditya) -> print("Aditya"))
        if "unterminated string literal" in msg or "eol while scanning" in msg:
            for q in ('"', "'"):
                if line.count(q) % 2 != 0:
                    repaired_line = line
                    for closer in (")", "]", "}"):
                        if line.rstrip().endswith(closer):
                            idx = line.rfind(closer)
                            repaired_line = line[:idx] + q + line[idx:]
                            break
                    else:
                        repaired_line = line + q

                    candidate = "\n".join(lines[:target_idx] + [repaired_line] + lines[target_idx + 1 :])
                    try:
                        ast.parse(candidate)
                        return candidate, f"Close the string literal with matching `{q}` on line {line_no}."
                    except SyntaxError:
                        pass

        # 2. Expected ':'
        if "expected ':'" in msg:
            repaired_line = line.rstrip() + ":"
            candidate = "\n".join(lines[:target_idx] + [repaired_line] + lines[target_idx + 1 :])
            try:
                ast.parse(candidate)
                return candidate, f"Add missing `:` at the end of statement on line {line_no}."
            except SyntaxError:
                pass

        # 3. Delimiter was never closed
        if "was never closed" in msg or "unmatched" in msg:
            for closer in (")", "]", "}"):
                repaired_line = line + closer
                candidate = "\n".join(lines[:target_idx] + [repaired_line] + lines[target_idx + 1 :])
                try:
                    ast.parse(candidate)
                    return candidate, f"Add closing `{closer}` on line {line_no}."
                except SyntaxError:
                    pass

        # 4. Single statement missing closing parenthesis
        if len(lines) == 1 and ("(" in line and not line.endswith(")")):
            candidate = line + ")"
            try:
                ast.parse(candidate)
                return candidate, "Add missing closing parenthesis."
            except SyntaxError:
                pass

        return code, "Correct the syntax at the highlighted line and keep indentation consistent."
