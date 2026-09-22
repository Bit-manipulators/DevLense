from __future__ import annotations

from pydantic import BaseModel, Field

from app.analysis.code_analysis_engine import CodeAnalysisResult
from app.config import Settings
from app.context.problem_context import ProblemContext
from app.execution.manager import DetailedExecutionResult
from app.testing.failure_analysis import FailureEvidence


class DiagnosisReport(BaseModel):
    expected_behavior: str
    actual_behavior: str
    failure_evidence_summary: str
    root_cause: str
    suggested_repair_strategy: str
    recommended_tests: list[str] = Field(default_factory=list)


class ReasoningEngine:
    """Answers structured diagnostic questions by synthesizing concrete evidence with expert rules."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings

    async def diagnose(
        self,
        *,
        context: ProblemContext,
        code: str,
        static_analysis: CodeAnalysisResult | None = None,
        exec_result: DetailedExecutionResult | None = None,
        failure_evidence: list[FailureEvidence] | None = None,
    ) -> DiagnosisReport:
        evidence_list = failure_evidence or []
        primary_failure = evidence_list[0] if evidence_list else None

        # 1. Expected behavior
        expected_behavior = self._derive_expected_behavior(context, primary_failure)

        # 2. Actual behavior
        actual_behavior = self._derive_actual_behavior(primary_failure, exec_result, static_analysis)

        # 3. Evidence summary
        evidence_summary = self._derive_evidence_summary(evidence_list, primary_failure, exec_result)

        # 4. Root cause
        root_cause = self._derive_root_cause(primary_failure, static_analysis, context)

        # 5. Repair strategy
        strategy = self._derive_repair_strategy(primary_failure, static_analysis, context)

        # 6. Recommended post-fix tests
        recommended_tests = self._derive_recommended_tests(context, primary_failure)

        return DiagnosisReport(
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior,
            failure_evidence_summary=evidence_summary,
            root_cause=root_cause,
            suggested_repair_strategy=strategy,
            recommended_tests=recommended_tests,
        )

    def _derive_expected_behavior(
        self, context: ProblemContext, failure: FailureEvidence | None
    ) -> str:
        if failure and failure.expected_output:
            return f"Given input `{failure.test_case_input}`, the program should produce `{failure.expected_output}`."
        if context.objective:
            return context.objective
        return "Program should execute cleanly, produce correct return values, and exit with status 0."

    def _derive_actual_behavior(
        self,
        failure: FailureEvidence | None,
        exec_result: DetailedExecutionResult | None,
        static: CodeAnalysisResult | None,
    ) -> str:
        if not failure:
            return "Program executed without detected runtime errors."

        ftype = failure.failure_type
        if ftype == "compilation":
            return f"Compilation failed before execution: {failure.stderr[:200]}"
        if ftype == "syntax":
            return f"Failed during lexical/syntax parsing: {failure.likely_root_cause}"
        if ftype == "timeout":
            return "Execution timed out after exceeding the maximum runtime limit (possible infinite loop or TLE)."
        if ftype == "runtime":
            return f"Process terminated abnormally with runtime error: {failure.likely_root_cause}"
        if ftype in ("incorrect_output", "edge_case_failure"):
            return f"Program returned `{failure.actual_output}` on input `{failure.test_case_input}`."

        return "Program exhibited unintended execution behavior."

    def _derive_evidence_summary(
        self,
        evidence_list: list[FailureEvidence],
        primary: FailureEvidence | None,
        exec_result: DetailedExecutionResult | None,
    ) -> str:
        if not primary:
            return "All test executions satisfied expected criteria."

        details = [f"Primary failure category: {primary.failure_type}."]
        if primary.test_case_input:
            details.append(f"Failing input: `{primary.test_case_input}`.")
        if primary.expected_output:
            details.append(f"Expected: `{primary.expected_output}`.")
        if primary.actual_output:
            details.append(f"Actual: `{primary.actual_output}`.")
        if primary.evidence:
            details.append(f"Diagnostic note: {primary.evidence}")

        if len(evidence_list) > 1:
            details.append(f"({len(evidence_list)} total failing test cases observed).")

        return " ".join(details)

    def _derive_root_cause(
        self,
        failure: FailureEvidence | None,
        static: CodeAnalysisResult | None,
        context: ProblemContext,
    ) -> str:
        if failure and failure.likely_root_cause:
            return failure.likely_root_cause
        if static and static.primary_finding:
            return static.primary_finding.root_cause
        return "Logic discrepancy between implementation and problem constraints."

    def _derive_repair_strategy(
        self,
        failure: FailureEvidence | None,
        static: CodeAnalysisResult | None,
        context: ProblemContext,
    ) -> str:
        if not failure:
            return "No modification required; existing code satisfies tests."

        ftype = failure.failure_type
        if ftype == "compilation":
            return "Correct the compiler-reported syntax error and missing delimiters."
        if ftype == "syntax":
            return "Adjust unclosed delimiters or Python indentation hierarchy."
        if ftype == "runtime":
            if "IndexError" in failure.stderr or "bounds" in failure.likely_root_cause:
                return "Ensure loop upper bound is strictly less than sequence length (0-indexed)."
            if "ZeroDivisionError" in failure.stderr:
                return "Add guard clause to ensure denominator is non-zero before division."
            return "Add defensive precondition guards and validate index/pointer boundaries."
        if ftype in ("incorrect_output", "edge_case_failure"):
            if context.problem_name == "Two Sum":
                return (
                    "Use a hash map to record seen element indices in a single pass. "
                    "Ensure duplicate numbers (e.g., [3,3] for target 6) do not overwrite index before lookup."
                )
            if context.problem_name == "Valid Parentheses":
                return "Use a stack to match opening brackets with corresponding closing brackets and check for emptiness at end."
            return "Refine conditional branches and loop termination criteria to match problem specification."
        if ftype == "wrong_algorithm":
            return "Replace nested iteration with an optimal O(N) single-pass or hash table approach."

        return "Apply targeted bugfix to address the observed failing test case."

    def _derive_recommended_tests(
        self, context: ProblemContext, failure: FailureEvidence | None
    ) -> list[str]:
        tests = []
        if failure and failure.test_case_input:
            tests.append(f"Re-run exact failing input: `{failure.test_case_input}`")
        if context.edge_cases:
            tests.extend(context.edge_cases[:2])
        tests.append("Verify all previously passing baseline examples remain intact.")
        return tests
