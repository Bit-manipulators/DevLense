from __future__ import annotations

import logging
from typing import Any

from app.analysis.code_analysis_engine import CodeAnalysisEngine
from app.config import Settings, get_settings
from app.context.problem_understanding import ProblemUnderstandingService
from app.execution.base import ExecutionService
from app.execution.manager import ExecutionManager
from app.languages.registry import LanguageRegistry
from app.reasoning.engine import ReasoningEngine
from app.repair.diff import DiffGenerator
from app.repair.engine import RepairEngine
from app.schemas.debug import DebugReport, DebugRequest, IterationRecord, ValidationSummary
from app.testing.generator import TestGenerationService
from app.validation.engine import ValidationEngine

logger = logging.getLogger("devlens.orchestrator")


class DebugOrchestrator:
    """Central orchestration service for evidence-driven debugging pipelines."""

    def __init__(
        self,
        execution_service: ExecutionService,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.execution_manager = ExecutionManager(execution_service)
        self.problem_service = ProblemUnderstandingService()
        self.reasoning_engine = ReasoningEngine(self.settings)
        self.validation_engine = ValidationEngine(self.execution_manager)

    async def debug(self, request: DebugRequest) -> DebugReport:
        logger.info(
            "Starting debug orchestration for language '%s', mode '%s'",
            request.language,
            request.mode,
        )

        # 1. Language Resolution (Strict routing, never defaults to python)
        canonical_lang = LanguageRegistry.resolve_language(explicit_language=request.language)

        # 2. Problem Understanding
        context = self.problem_service.analyze(
            problem_statement=request.problem_statement,
            constraints=request.constraints,
            code=request.code,
            language=canonical_lang,
            mode=request.mode,
            user_test_cases=request.test_cases,
        )

        # 3. Static & Complexity Analysis
        static_analysis = CodeAnalysisEngine.analyze(
            code=request.code,
            language=canonical_lang,
            error_message=request.error_message,
            question=request.question,
            constraints=context.constraints,
        )

        # 4. Generate Test Suite
        user_tests = request.test_cases or []
        if request.stdin or request.expected_output:
            user_tests.append({"input": request.stdin or "", "expected_output": request.expected_output or ""})

        test_suite = TestGenerationService.generate_tests(
            context=context,
            max_tests=self.settings.max_generated_tests,
            user_test_cases=user_tests,
        )

        # 5. Baseline Validation on Initial Code
        initial_val = await self.validation_engine.validate(
            code=request.code,
            language=canonical_lang,
            context=context,
            tests=test_suite,
        )

        # If original code passes all tests, has no bottleneck, and has no static defect
        has_bottleneck = bool(static_analysis.complexity and static_analysis.complexity.is_bottleneck)
        has_static_defect = bool(
            static_analysis.primary_finding
            and static_analysis.primary_finding.severity in ("high", "critical")
            and not static_analysis.primary_finding.summary.startswith("Code Structure Verified")
            and "No Static Defects Detected" not in static_analysis.primary_finding.summary
        )
        if initial_val.validated and not has_bottleneck and not has_static_defect and not request.error_message:
            logger.info("Original code passed all validation tests.")
            return DebugReport(
                status="passed",
                language=canonical_lang,
                problem_summary=context.objective,
                root_cause="No defects detected; code passed all static and sandboxed validation tests.",
                failure_type="none",
                evidence=[],
                original_code=request.code,
                corrected_code=request.code,
                diff="",
                affected_lines=[],
                iterations=[],
                tests_run=initial_val.tests_run,
                tests_passed=initial_val.tests_passed,
                tests_failed=0,
                validation=ValidationSummary(
                    compile=initial_val.compile_passed,
                    runtime=initial_val.runtime_passed,
                    tests=True,
                ),
                complexity=static_analysis.complexity,
            )

        # 6. Iterative Diagnosis & Repair Loop
        current_code = request.code
        current_failures = initial_val.failures
        iterations: list[IterationRecord] = []
        final_status = "failed"
        corrected_code = request.code
        final_diff = ""
        final_affected_lines: list[int] = []
        final_root_cause = current_failures[0].likely_root_cause if current_failures else "Unknown error"
        final_failure_type = current_failures[0].failure_type if current_failures else "incorrect_output"
        last_val = initial_val

        max_iters = min(self.settings.max_debug_iterations, 5)

        for iteration_idx in range(1, max_iters + 1):
            logger.info("Running debug iteration %d/%d", iteration_idx, max_iters)

            # A. Reasoning Engine Diagnosis
            diagnosis = await self.reasoning_engine.diagnose(
                context=context,
                code=current_code,
                static_analysis=static_analysis,
                failure_evidence=current_failures,
            )
            final_root_cause = diagnosis.root_cause

            # B. Repair Engine Generation
            repair_res = RepairEngine.repair(
                context=context,
                code=current_code,
                diagnosis=diagnosis,
                static_analysis=static_analysis,
                failure_evidence=current_failures,
            )

            # C. Sandboxed Fix Validation
            candidate_code = repair_res.corrected_code
            val_res = await self.validation_engine.validate(
                code=candidate_code,
                language=canonical_lang,
                context=context,
                tests=test_suite,
            )
            last_val = val_res

            iteration_diff = DiffGenerator.generate_unified_diff(
                request.code, candidate_code, filename=LanguageRegistry.get(canonical_lang).filename
            )

            record = IterationRecord(
                iteration=iteration_idx,
                diagnosis=diagnosis.root_cause,
                suggested_fix=repair_res.explanation,
                diff=iteration_diff,
                tests_passed=val_res.tests_passed,
                tests_failed=val_res.tests_failed,
                validated=val_res.validated,
            )
            iterations.append(record)

            if val_res.validated:
                logger.info("Candidate fix validated successfully in iteration %d.", iteration_idx)
                final_status = "fixed"
                corrected_code = candidate_code
                final_diff = iteration_diff
                final_affected_lines = DiffGenerator.compute_affected_lines(request.code, candidate_code)
                break
            else:
                # Prepare evidence for next iteration if retryable
                current_code = candidate_code
                current_failures = val_res.failures
                static_analysis = val_res.static_analysis

        if final_status != "fixed":
            # If after max iterations code did not validate, compute diff against best effort
            if corrected_code == request.code and iterations:
                # Use best effort candidate from iteration 1
                corrected_code = iterations[0].diff and request.code  # keep original if not validated
            final_status = "needs_review" if iterations and iterations[-1].tests_passed > 0 else "failed"

        return DebugReport(
            status=final_status,
            language=canonical_lang,
            problem_summary=context.objective,
            root_cause=final_root_cause,
            failure_type=final_failure_type,
            evidence=initial_val.failures,
            original_code=request.code,
            corrected_code=corrected_code,
            diff=final_diff,
            affected_lines=final_affected_lines,
            iterations=iterations,
            tests_run=last_val.tests_run,
            tests_passed=last_val.tests_passed,
            tests_failed=last_val.tests_failed,
            validation=ValidationSummary(
                compile=last_val.compile_passed,
                runtime=last_val.runtime_passed,
                tests=last_val.validated,
            ),
            complexity=static_analysis.complexity if static_analysis else last_val.static_analysis.complexity,
        )
