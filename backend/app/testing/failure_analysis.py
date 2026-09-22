from __future__ import annotations

import re
from typing import Literal
from pydantic import BaseModel

from app.analysis.code_analysis_engine import CodeAnalysisResult
from app.context.problem_context import ProblemContext
from app.execution.manager import DetailedExecutionResult
from app.testing.comparator import OutputComparator
from app.testing.generator import TestCase

FailureType = Literal[
    "compilation",
    "syntax",
    "runtime",
    "incorrect_output",
    "timeout",
    "memory_resource",
    "wrong_algorithm",
    "edge_case_failure",
    "format_mismatch",
]


class FailureEvidence(BaseModel):
    failure_type: FailureType
    test_case_input: str
    expected_output: str | None = None
    actual_output: str | None = None
    exit_code: int = 0
    stderr: str = ""
    evidence: str = ""
    likely_root_cause: str = ""


class FailureAnalysisService:
    """Diagnoses and classifies execution and static failures into concrete evidence."""

    @classmethod
    def analyze_failure(
        cls,
        *,
        context: ProblemContext,
        code: str,
        static_analysis: CodeAnalysisResult | None = None,
        exec_result: DetailedExecutionResult | None = None,
        test_case: TestCase | None = None,
    ) -> FailureEvidence:
        tc_input = test_case.input_raw if test_case else ""
        expected = test_case.expected_output if test_case else None
        actual = exec_result.stdout.strip() if exec_result else ""
        stderr = exec_result.stderr.strip() if exec_result else ""
        exit_code = exec_result.exit_code if exec_result else 0

        # 1. Compilation failure
        if exec_result and exec_result.status == "compile_error":
            root_cause = cls._extract_compile_cause(stderr, context.language)
            return FailureEvidence(
                failure_type="compilation",
                test_case_input=tc_input,
                expected_output=expected,
                actual_output=actual,
                exit_code=exit_code,
                stderr=stderr,
                evidence=f"Compiler output reported: {stderr[:300]}",
                likely_root_cause=root_cause,
            )

        # 2. Syntax parse error from static analysis
        if static_analysis and not static_analysis.syntax_valid:
            first_err = static_analysis.syntax_errors[0] if static_analysis.syntax_errors else {}
            msg = str(first_err.get("message", "Syntax error"))
            return FailureEvidence(
                failure_type="syntax",
                test_case_input=tc_input,
                expected_output=expected,
                actual_output=actual,
                exit_code=exit_code,
                stderr=stderr,
                evidence=f"Syntax analysis failed at line {first_err.get('line', '?')}: {msg}",
                likely_root_cause=msg,
            )

        # 3. Timeout / TLE
        if exec_result and exec_result.status == "timeout":
            # Check if complexity is quadratic or exponential
            is_algo_bottleneck = (
                static_analysis.complexity.is_bottleneck
                if (static_analysis and static_analysis.complexity)
                else False
            )
            ftype: FailureType = "wrong_algorithm" if is_algo_bottleneck else "timeout"
            return FailureEvidence(
                failure_type=ftype,
                test_case_input=tc_input,
                expected_output=expected,
                actual_output=actual,
                exit_code=exit_code,
                stderr=stderr,
                evidence="Process exceeded sandbox execution time limit (5s).",
                likely_root_cause=(
                    "The algorithm has excessive time complexity or contains an infinite loop, "
                    "causing execution to timeout."
                ),
            )

        # 4. Out of Memory / Resource limit
        if exec_result and exec_result.status == "resource_error":
            return FailureEvidence(
                failure_type="memory_resource",
                test_case_input=tc_input,
                expected_output=expected,
                actual_output=actual,
                exit_code=exit_code,
                stderr=stderr,
                evidence=f"Resource error: {stderr}",
                likely_root_cause="Memory or PID limit exceeded during execution.",
            )

        # 5. Runtime exception (IndexError, ZeroDivisionError, Segfault, NPE)
        if exec_result and (exec_result.status == "runtime_error" or exit_code != 0):
            root_cause = cls._extract_runtime_cause(stderr, context.language)
            return FailureEvidence(
                failure_type="runtime",
                test_case_input=tc_input,
                expected_output=expected,
                actual_output=actual,
                exit_code=exit_code,
                stderr=stderr,
                evidence=f"Runtime error with exit code {exit_code}: {stderr[:300]}",
                likely_root_cause=root_cause,
            )

        # 6. Incorrect output (logical error)
        if expected is not None:
            matched, comp_msg = OutputComparator.compare(expected, actual)
            if not matched:
                # Differentiate edge case failure vs general incorrect output
                is_edge = test_case.category in ("edge", "boundary") if test_case else False
                failure_type: FailureType = "edge_case_failure" if is_edge else "incorrect_output"

                root_cause = (
                    f"Logical bug in solution logic. On input `{tc_input}`, expected `{expected}` "
                    f"but program produced `{actual}`."
                )

                return FailureEvidence(
                    failure_type=failure_type,
                    test_case_input=tc_input,
                    expected_output=expected,
                    actual_output=actual,
                    exit_code=0,
                    stderr=stderr,
                    evidence=comp_msg,
                    likely_root_cause=root_cause,
                )

        # 7. Static finding only (e.g. potential bug detected)
        if static_analysis and static_analysis.primary_finding:
            finding = static_analysis.primary_finding
            return FailureEvidence(
                failure_type="incorrect_output",
                test_case_input=tc_input,
                expected_output=expected,
                actual_output=actual,
                exit_code=0,
                stderr="",
                evidence=finding.explanation,
                likely_root_cause=finding.root_cause,
            )

        return FailureEvidence(
            failure_type="incorrect_output",
            test_case_input=tc_input,
            expected_output=expected,
            actual_output=actual,
            exit_code=0,
            stderr="",
            evidence="Code behavior did not satisfy specification requirements.",
            likely_root_cause="Unspecified logic discrepancy.",
        )

    @staticmethod
    def _extract_compile_cause(stderr: str, language: str) -> str:
        if "expected ';'" in stderr:
            return "Missing semicolon ';' in statement."
        if "undefined reference" in stderr:
            return "Unresolved symbol or missing library definition."
        if "SyntaxError" in stderr or "IndentationError" in stderr:
            for line in stderr.splitlines():
                if "SyntaxError:" in line or "IndentationError:" in line:
                    return line.strip()
        m = re.search(r"error:\s*(.+)", stderr)
        if m:
            return m.group(1).strip()
        return "Compilation failed due to compiler errors."

    @staticmethod
    def _extract_runtime_cause(stderr: str, language: str) -> str:
        for err_type in (
            "SyntaxError",
            "ReferenceError",
            "TypeError",
            "RangeError",
            "IndexError",
            "ZeroDivisionError",
            "KeyError",
            "ValueError",
            "NullPointerException",
            "ArrayIndexOutOfBoundsException",
            "Segmentation fault",
            "core dumped",
        ):
            if err_type in stderr:
                m = re.search(rf"{err_type}(?::\s*.+)?", stderr)
                return m.group(0).strip() if m else err_type
        filtered_lines = [
            line.strip()
            for line in stderr.splitlines()
            if line.strip() and not line.strip().startswith("Node.js v")
        ]
        return filtered_lines[-1] if filtered_lines else "Abnormal process termination during runtime execution."

