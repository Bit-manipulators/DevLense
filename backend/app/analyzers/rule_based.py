from __future__ import annotations

import ast
import re

from app.analyzers.base import AnalysisFinding, AnalyzerProvider


class RuleBasedAnalyzer(AnalyzerProvider):
    """Deterministic first-pass diagnostics that work without a model or API key.

    These rules intentionally report *likely* faults rather than overstate what a
    lightweight static pass can prove.
    """

    async def analyze(
        self, language: str, code: str, error_message: str = "", question: str = ""
    ) -> AnalysisFinding:
        handlers = {
            "python": self._analyze_python,
            "cpp": self._analyze_cpp,
            "javascript": self._analyze_javascript,
            "java": self._analyze_java,
        }
        return handlers[language](code, error_message, question)

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

    def _no_definite_match(self, code: str, language: str) -> AnalysisFinding:
        return self._finding(
            summary="No definite fault matched the local rules",
            severity="low",
            root_cause=(
                "The rule-based analyzer could not prove a common issue from the supplied code and error."
            ),
            explanation=(
                f"DevLens ran its lightweight {language} checks, but this is not a full compiler or "
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

    def _analyze_python(self, code: str, error: str, _: str) -> AnalysisFinding:
        try:
            ast.parse(code)
        except (SyntaxError, IndentationError) as exc:
            line = exc.lineno or 1
            is_indent = isinstance(exc, IndentationError)
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
                suggested_fix="Correct the syntax at the highlighted line and keep indentation consistent.",
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
            corrected = re.sub(r"/\s*0(?:\D|$)", "/ denominator  # ensure denominator is non-zero\\n", code, count=1)
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

        if "NameError" in error:
            match = re.search(r"name ['\"](?P<name>\w+)['\"] is not defined", error)
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

        if "IndexError" in error:
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

        return self._no_definite_match(code, "Python")

    def _analyze_cpp(self, code: str, error: str, _: str) -> AnalysisFinding:
        array_loop = re.search(
            r"(?P<array>\w+)\s*\[\s*(?P<size>\d+)\s*\][\s\S]{0,500}?"
            r"for\s*\(\s*(?:int|size_t|long)\s+(?P<index>\w+)\s*=\s*0\s*;\s*"
            r"(?P=index)\s*<=\s*(?P<bound>\d+)\s*;[\s\S]{0,200}?"
            r"(?P=array)\s*\[\s*(?P=index)\s*\]",
            code,
        )
        if array_loop:
            size = int(array_loop.group("size"))
            bound = int(array_loop.group("bound"))
            if bound >= size:
                loop_line = code[: array_loop.start()].count("\n") + 1
                old = f"{array_loop.group('index')} <= {bound}"
                new = f"{array_loop.group('index')} < {size}"
                return self._finding(
                    summary="Possible array index out of bounds",
                    severity="high",
                    root_cause=(
                        f"The loop condition allows index {bound}, but {array_loop.group('array')} has valid indices 0 through {size - 1}."
                    ),
                    explanation=(
                        "C++ does not automatically check native array bounds. Reading past the array is undefined "
                        "behavior and can cause a segmentation fault."
                    ),
                    code=code,
                    suggested_fix=f"Replace `{old}` with `{new}`.",
                    corrected_code=code.replace(old, new, 1),
                    affected_lines=[loop_line],
                    confidence=0.96,
                    steps=[
                        "Use a strict `<` bound for an array of this size.",
                        "Prefer std::array or std::vector::at during debugging for bounds checks.",
                        "Compile with warnings enabled and rerun in the isolated sandbox.",
                    ],
                )

        null_match = re.search(r"(?:\w+\s*\*\s*)(?P<name>\w+)\s*=\s*(?:nullptr|NULL|0)\s*;[\s\S]{0,400}?\b(?P=name)\s*->", code)
        if null_match:
            line = code[: null_match.start()].count("\n") + 1
            name = null_match.group("name")
            return self._finding(
                summary="Null pointer dereference",
                severity="critical",
                root_cause=f"Pointer `{name}` is initialized to null and later dereferenced.",
                explanation="Dereferencing a null pointer invokes undefined behavior and commonly causes a segmentation fault.",
                code=code,
                suggested_fix=f"Initialize `{name}` to a valid object or guard it with `if ({name} != nullptr)` before dereferencing.",
                affected_lines=[line],
                confidence=0.97,
            )

        semicolon_line = self._line_of(code, r"(?:cout|return\s+\d+|int\s+\w+\s*=.+)\s*\n")
        if "expected ';'" in error.lower() and semicolon_line:
            return self._finding(
                summary="Missing C++ semicolon",
                severity="high",
                root_cause="The compiler reports a statement that is not terminated with `;`.",
                explanation="Most C++ statements must end with a semicolon.",
                code=code,
                suggested_fix="Add a semicolon at the compiler-reported statement.",
                affected_lines=[semicolon_line],
                confidence=0.9,
            )

        if re.search(r"/\s*0(?:\D|$)", code):
            line = self._line_of(code, r"/\s*0(?:\D|$)")
            return self._finding(
                summary="Division by zero",
                severity="high",
                root_cause="An expression divides by literal zero.",
                explanation="Integer division by zero is undefined behavior in C++.",
                code=code,
                suggested_fix="Validate the denominator before performing the division.",
                affected_lines=[line] if line else [],
                confidence=0.99,
            )
        return self._no_definite_match(code, "C++")

    def _analyze_javascript(self, code: str, error: str, _: str) -> AnalysisFinding:
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
        if "ReferenceError" in error:
            name_match = re.search(r"(?P<name>\w+) is not defined", error)
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

    def _analyze_java(self, code: str, error: str, _: str) -> AnalysisFinding:
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
        if re.search(r"/\s*0(?:\D|$)", code):
            line = self._line_of(code, r"/\s*0(?:\D|$)")
            return self._finding(
                summary="Division by zero",
                severity="high",
                root_cause="An expression divides by literal zero.",
                explanation="Integer division by zero throws ArithmeticException in Java.",
                code=code,
                suggested_fix="Check that the denominator is non-zero before dividing.",
                affected_lines=[line] if line else [],
                confidence=0.99,
            )
        return self._no_definite_match(code, "Java")

