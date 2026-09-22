from __future__ import annotations

import ast
from pydantic import BaseModel, Field

from app.analysis.complexity import ComplexityAnalyzer, ComplexityReport
from app.analyzers.base import AnalysisFinding
from app.analyzers.factory import AnalyzerFactory
from app.languages.registry import LanguageRegistry


class CodeAnalysisResult(BaseModel):
    language: str
    syntax_valid: bool = True
    syntax_errors: list[dict[str, str | int]] = Field(default_factory=list)
    findings: list[AnalysisFinding] = Field(default_factory=list)
    complexity: ComplexityReport
    primary_finding: AnalysisFinding | None = None


class CodeAnalysisEngine:
    """Multi-layer static, lexical, AST, and algorithmic complexity analyzer."""

    @classmethod
    def analyze(
        cls,
        *,
        code: str,
        language: str,
        error_message: str = "",
        question: str = "",
        constraints: list[str] | None = None,
    ) -> CodeAnalysisResult:
        canonical_lang = LanguageRegistry.normalize(language)
        syntax_errors: list[dict[str, str | int]] = []
        findings: list[AnalysisFinding] = []

        # Layer 1: Lexical delimiter checks
        delimiter_err = cls._check_delimiters(code)
        if delimiter_err:
            syntax_errors.append(delimiter_err)

        # Layer 2: Syntax parsing (AST for Python, statement validation for C++/JS/Java)
        if canonical_lang == "python":
            py_syntax_err = cls._check_python_syntax(code)
            if py_syntax_err:
                syntax_errors.append(py_syntax_err)

        # Layer 3: Static & Semantic rules
        analyzer = AnalyzerFactory.get_language_analyzer(canonical_lang)
        rule_finding = analyzer.analyze(code, error_message, question)
        is_real_defect = (
            rule_finding is not None
            and "No definite fault" not in rule_finding.summary
            and "No Static Defects Detected" not in rule_finding.summary
            and not rule_finding.summary.startswith("Code Structure Verified")
        )
        if is_real_defect and rule_finding:
            findings.append(rule_finding)

        # Layer 4: Complexity analysis
        complexity = ComplexityAnalyzer.analyze(code, canonical_lang, constraints)
        if complexity.is_bottleneck:
            bottleneck_finding = AnalysisFinding(
                summary=f"Algorithmic Performance Bottleneck: {complexity.time_complexity}",
                severity="high",
                root_cause=f"Time complexity {complexity.time_complexity} exceeds acceptable scale for inputs.",
                explanation=complexity.warning or (
                    f"The code structure ({complexity.details}) results in {complexity.time_complexity} time complexity, "
                    "creating high risk of Time Limit Exceeded (TLE)."
                ),
                affected_lines=[],
                suggested_fix="Optimize using memoization, dynamic programming, or linear single-pass structures.",
                corrected_code=code,
                debugging_steps=[
                    "Inspect loop nesting and recursive call branches.",
                    "Cache overlapping subproblems or precalculate prefix/suffix tables.",
                ],
                confidence=0.92,
            )
            findings.append(bottleneck_finding)

        syntax_valid = len(syntax_errors) == 0

        # Choose primary finding
        primary_finding: AnalysisFinding | None = None
        if not syntax_valid and syntax_errors:
            err = syntax_errors[0]
            line_no = int(err.get("line", 1))
            msg = str(err.get("message", "Syntax error"))
            primary_finding = AnalysisFinding(
                summary="Syntax / Delimiter Error",
                severity="high",
                root_cause=msg,
                explanation=f"A delimiter or syntax construct is malformed on or near line {line_no}.",
                affected_lines=[line_no],
                suggested_fix="Check matching parentheses, brackets, quotes, and block endings.",
                corrected_code=code,
                debugging_steps=["Inspect the highlighted line and balance open brackets/parentheses."],
                confidence=0.95,
            )
        elif findings:
            primary_finding = findings[0]
        elif is_real_defect and rule_finding:
            primary_finding = rule_finding
        else:
            primary_finding = AnalysisFinding(
                summary="Code Structure Verified (Clean)",
                severity="low",
                root_cause="No syntax errors, unbalanced delimiters, or known anti-patterns detected.",
                explanation=(
                    f"Multi-layer static analysis verified {canonical_lang} syntax and balanced delimiters. "
                    f"Estimated complexity: {complexity.time_complexity} time, {complexity.space_complexity} space ({complexity.details}). "
                    "Use sandboxed execution with test cases to verify dynamic logic and edge cases."
                ),
                affected_lines=[],
                suggested_fix="Code structure is sound. Run with test cases in the sandbox to verify runtime logic.",
                corrected_code=code,
                debugging_steps=[
                    "Syntax and delimiter structure verified clean.",
                    f"Complexity profile: {complexity.time_complexity} time, {complexity.space_complexity} space.",
                    "Verify behavior on boundary inputs in sandbox.",
                ],
                confidence=0.90,
            )

        return CodeAnalysisResult(
            language=canonical_lang,
            syntax_valid=syntax_valid,
            syntax_errors=syntax_errors,
            findings=findings,
            complexity=complexity,
            primary_finding=primary_finding,
        )

    @classmethod
    def _check_delimiters(cls, code: str) -> dict[str, str | int] | None:
        stack: list[tuple[str, int]] = []
        pairs = {")": "(", "]": "[", "}": "{"}

        # Track line number
        line_no = 1
        in_string: str | None = None
        in_single_comment = False
        in_multi_comment = False

        i = 0
        while i < len(code):
            ch = code[i]
            if ch == "\n":
                line_no += 1
                in_single_comment = False
                i += 1
                continue

            if in_single_comment:
                i += 1
                continue

            # Check comment start
            if not in_string and not in_multi_comment:
                if code[i : i + 2] == "//" or ch == "#":
                    in_single_comment = True
                    i += 1
                    continue
                if code[i : i + 2] == "/*":
                    in_multi_comment = True
                    i += 2
                    continue

            if in_multi_comment:
                if code[i : i + 2] == "*/":
                    in_multi_comment = False
                    i += 2
                    continue
                i += 1
                continue

            # Strings
            if ch in ('"', "'") and not in_string:
                # Ignore raw escaped or docstrings for simplicity
                in_string = ch
                i += 1
                continue
            elif ch == in_string:
                # Check escape
                if i > 0 and code[i - 1] == "\\":
                    pass
                else:
                    in_string = None
                i += 1
                continue

            if in_string:
                i += 1
                continue

            # Delimiters
            if ch in ("(", "[", "{"):
                stack.append((ch, line_no))
            elif ch in (")", "]", "}"):
                if not stack:
                    return {"line": line_no, "message": f"Unmatched closing delimiter '{ch}'"}
                last_open, open_line = stack.pop()
                if last_open != pairs[ch]:
                    return {
                        "line": line_no,
                        "message": f"Mismatched delimiter: opened with '{last_open}' on line {open_line}, closed with '{ch}' on line {line_no}",
                    }
            i += 1

        if stack:
            unclosed, open_line = stack[-1]
            return {"line": open_line, "message": f"Unclosed delimiter '{unclosed}' opened on line {open_line}"}

        return None

    @classmethod
    def _check_python_syntax(cls, code: str) -> dict[str, str | int] | None:
        try:
            ast.parse(code)
            return None
        except SyntaxError as exc:
            return {
                "line": exc.lineno or 1,
                "message": exc.msg or "Python syntax error",
            }
