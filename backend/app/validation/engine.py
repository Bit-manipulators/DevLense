from __future__ import annotations

from pydantic import BaseModel, Field

from app.analysis.code_analysis_engine import CodeAnalysisEngine, CodeAnalysisResult
from app.context.problem_context import ProblemContext
from app.execution.manager import DetailedExecutionResult, ExecutionManager
from app.languages.registry import LanguageRegistry
from app.testing.comparator import OutputComparator
from app.testing.failure_analysis import FailureAnalysisService, FailureEvidence
from app.testing.generator import TestCase
from app.testing.harness import TestHarnessBuilder


class ValidationResult(BaseModel):
    validated: bool
    compile_passed: bool = True
    runtime_passed: bool = True
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    failures: list[FailureEvidence] = Field(default_factory=list)
    static_analysis: CodeAnalysisResult | None = None


class ValidationEngine:
    """Validates candidate fixes by compiling, executing, and comparing test outcomes."""

    def __init__(self, execution_manager: ExecutionManager):
        self.execution_manager = execution_manager

    async def validate(
        self,
        *,
        code: str,
        language: str,
        context: ProblemContext,
        tests: list[TestCase],
    ) -> ValidationResult:
        canonical_lang = LanguageRegistry.normalize(language)

        # 1. Run static analysis on candidate code
        static_res = CodeAnalysisEngine.analyze(
            code=code,
            language=canonical_lang,
            constraints=context.constraints,
        )

        failures: list[FailureEvidence] = []
        tests_passed = 0
        tests_run = 0
        compile_passed = True
        runtime_passed = True

        if not static_res.syntax_valid:
            compile_passed = False
            failures.append(
                FailureAnalysisService.analyze_failure(
                    context=context,
                    code=code,
                    static_analysis=static_res,
                )
            )
            return ValidationResult(
                validated=False,
                compile_passed=False,
                runtime_passed=False,
                tests_run=0,
                tests_passed=0,
                tests_failed=1,
                failures=failures,
                static_analysis=static_res,
            )

        # 2. Run tests in sandbox
        for test in tests:
            tests_run += 1
            exec_code, stdin_data = TestHarnessBuilder.prepare_executable_code(
                code, canonical_lang, test, context
            )

            exec_result: DetailedExecutionResult = await self.execution_manager.execute(
                canonical_lang, exec_code, stdin_data
            )

            if exec_result.status == "compile_error":
                compile_passed = False
                runtime_passed = False
                failures.append(
                    FailureAnalysisService.analyze_failure(
                        context=context,
                        code=code,
                        static_analysis=static_res,
                        exec_result=exec_result,
                        test_case=test,
                    )
                )
                break  # Stop immediately on compilation failure

            if not exec_result.success:
                runtime_passed = False
                failures.append(
                    FailureAnalysisService.analyze_failure(
                        context=context,
                        code=code,
                        static_analysis=static_res,
                        exec_result=exec_result,
                        test_case=test,
                    )
                )
                continue

            # Check output against expected
            if test.expected_output is not None:
                matched, _ = OutputComparator.compare(test.expected_output, exec_result.stdout)
                if not matched:
                    failures.append(
                        FailureAnalysisService.analyze_failure(
                            context=context,
                            code=code,
                            static_analysis=static_res,
                            exec_result=exec_result,
                            test_case=test,
                        )
                    )
                    continue

            tests_passed += 1

        tests_failed = len(failures)
        validated = (tests_failed == 0 and compile_passed and runtime_passed and tests_run > 0) or (
            tests_run == 0 and static_res.syntax_valid
        )

        return ValidationResult(
            validated=validated,
            compile_passed=compile_passed,
            runtime_passed=runtime_passed,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            failures=failures,
            static_analysis=static_res,
        )
