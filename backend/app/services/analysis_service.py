from __future__ import annotations

import logging
from typing import Any

from app.analyzers.base import AnalysisFinding, AnalyzerProvider
from app.analyzers.rule_based import RuleBasedAnalyzer

logger = logging.getLogger("devlens.analysis")


class AnalysisService:
    """Coordinates the configured analyzer, evidence-driven engine, and safe fallback."""

    def __init__(
        self,
        analyzer: AnalyzerProvider,
        debug_orchestrator: Any = None,
    ):
        self.analyzer = analyzer
        self.debug_orchestrator = debug_orchestrator
        self.fallback = RuleBasedAnalyzer()

    async def analyze(
        self, language: str, code: str, error_message: str = "", question: str = ""
    ) -> AnalysisFinding:
        # Priority 1: Configured Analyzer (deterministic static rules or LLM)
        try:
            finding = await self.analyzer.analyze(language, code, error_message, question)
            is_generic = (
                "No definite fault" in finding.summary
                or "No Static Defects Detected" in finding.summary
                or finding.summary.startswith("Code Structure Verified")
            )
            if not is_generic:
                return finding
        except Exception as exc:
            logger.warning(
                "Configured analyzer (%s) failed: %s",
                type(self.analyzer).__name__,
                exc,
            )

        # Priority 2: Evidence-Driven Debug Orchestrator (real compiler/sandbox execution)
        if self.debug_orchestrator:
            try:
                from app.schemas.debug import DebugRequest

                req = DebugRequest(
                    language=language,
                    code=code,
                    error_message=error_message or "",
                    question=question or "",
                    problem_statement=question or "",
                    mode="general",
                )

                report = await self.debug_orchestrator.debug(req)
                return self._report_to_finding(report, language, code)
            except Exception as exc:
                logger.warning("Debug orchestrator in analyze encountered error: %s", exc)

        # Priority 3: Multi-Layer Static Analysis Engine
        from app.analysis.code_analysis_engine import CodeAnalysisEngine

        result = CodeAnalysisEngine.analyze(
            code=code,
            language=language,
            error_message=error_message,
            question=question,
        )
        if result.primary_finding:
            is_generic = (
                "No definite fault" in result.primary_finding.summary
                or "No Static Defects Detected" in result.primary_finding.summary
                or result.primary_finding.summary.startswith("Code Structure Verified")
            )
            if not is_generic:
                return result.primary_finding

        # Structured verified clean finding
        return AnalysisFinding(
            summary="Code Structure Verified (No Defects Detected)",
            severity="low",
            root_cause="No syntax errors, unbalanced delimiters, or known anti-patterns detected.",
            explanation=(
                f"Multi-layer static analysis verified {language} syntax and structure. "
                f"Estimated complexity: {result.complexity.time_complexity} time, {result.complexity.space_complexity} space. "
                "Delimiters are balanced and no static defects were identified."
            ),
            affected_lines=[],
            suggested_fix="Code structure is sound. Run with specific inputs to verify runtime behavior.",
            corrected_code=code,
            debugging_steps=[
                "Code structure and syntax verified clean.",
                f"Complexity: {result.complexity.time_complexity} time, {result.complexity.space_complexity} space.",
                "Verify behavior on boundary inputs in the sandbox.",
            ],
            confidence=0.90,
        )

    def _report_to_finding(self, report: Any, language: str, code: str) -> AnalysisFinding:
        # Determine severity
        if report.status in ("failed", "needs_review"):
            if report.failure_type in ("compilation", "runtime_error", "timeout", "resource_limit"):
                severity = "critical"
            else:
                severity = "high"
        elif report.complexity and report.complexity.is_bottleneck:
            severity = "high"
        else:
            severity = "low"

        # Summary
        if report.failure_type == "compilation":
            summary = f"Compilation Error: {report.root_cause}"
        elif report.failure_type == "runtime_error":
            summary = f"Runtime Exception: {report.root_cause}"
        elif report.failure_type == "timeout":
            summary = "Execution Timed Out (Possible Infinite Loop or Bottleneck)"
        elif report.complexity and report.complexity.is_bottleneck:
            summary = f"Performance Bottleneck ({report.complexity.time_complexity}): TLE Risk"
        elif report.status == "passed":
            summary = "Code Structure & Execution Verified: Clean (No Defects Detected)"
        else:
            summary = report.problem_summary or f"Debug analysis: {report.root_cause}"

        # Explanation
        explanation_parts = []
        if report.evidence:
            for ev in report.evidence[:2]:
                if ev.stderr:
                    explanation_parts.append(f"Execution Output:\n{ev.stderr.strip()}")
                elif ev.evidence:
                    explanation_parts.append(ev.evidence)
        elif report.iterations:
            explanation_parts.append(f"Diagnosis: {report.iterations[-1].diagnosis}")

        if report.complexity:
            c = report.complexity
            explanation_parts.append(
                f"Complexity: {c.time_complexity} time, {c.space_complexity} space ({c.details})"
            )
            if c.warning:
                explanation_parts.append(f"Warning: {c.warning}")

        if not explanation_parts:
            explanation_parts.append(
                f"Sandboxed execution and multi-layer analysis completed for {language}."
            )

        explanation = "\n\n".join(explanation_parts)

        # Debugging steps
        debugging_steps = []
        if report.iterations:
            for it in report.iterations:
                debugging_steps.append(f"Iteration {it.iteration}: {it.suggested_fix}")
        else:
            debugging_steps = [
                f"Ran {report.tests_run} tests: {report.tests_passed} passed, {report.tests_failed} failed.",
                "Verify variable bounds and edge cases in the isolated execution sandbox.",
            ]

        root_cause = report.root_cause or "No root cause defect identified."
        corrected_code = report.corrected_code or code

        # Suggested fix
        suggested_fix = ""
        if report.diff:
            suggested_fix = f"Apply validated patch:\n{report.diff}"
        elif report.iterations and report.iterations[-1].suggested_fix:
            suggested_fix = report.iterations[-1].suggested_fix

        if report.complexity and report.complexity.is_bottleneck:
            root_cause = f"Exponential or high time complexity ({report.complexity.time_complexity}): {report.complexity.details}. High risk of Time Limit Exceeded (TLE)."
            from app.context.problem_understanding import ProblemUnderstandingService
            from app.repair.engine import RepairEngine
            ctx = ProblemUnderstandingService().analyze(code=code, language=language)
            algo_fixed, algo_note = RepairEngine._repair_algorithmic(code, ctx, None)
            if algo_fixed:
                suggested_fix = f"{algo_note}\n\nOptimized Implementation:\n{algo_fixed}"
                corrected_code = algo_fixed
            elif not suggested_fix:
                suggested_fix = "Optimize recursion using dynamic programming, an iterative loop, or memoization."

        if not suggested_fix:
            suggested_fix = (
                "No repair required. Code structure and execution are verified clean."
                if report.status == "passed"
                else "Inspect compiler or runtime diagnostic details."
            )

        confidence = (
            0.95
            if (report.status in ("passed", "fixed") or report.failure_type == "compilation")
            else 0.88
        )

        return AnalysisFinding(
            summary=summary,
            severity=severity,
            root_cause=root_cause,
            explanation=explanation,
            affected_lines=report.affected_lines,
            suggested_fix=suggested_fix,
            corrected_code=corrected_code,
            debugging_steps=debugging_steps,
            confidence=confidence,
        )

