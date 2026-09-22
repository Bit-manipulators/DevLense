from __future__ import annotations

import pytest

from app.analysis.code_analysis_engine import CodeAnalysisEngine
from app.benchmarks.suite import BenchmarkSuite
from app.execution.base import ExecutionOutput, ExecutionService
from app.orchestrator.debug_orchestrator import DebugOrchestrator
from app.schemas.debug import DebugRequest


class SmartBenchmarkSandbox(ExecutionService):
    """Sandbox simulator that accurately executes Python code with eval for functions."""

    async def execute(self, language: str, code: str, stdin: str = "") -> ExecutionOutput:
        # Check syntax error
        if "Unclosed" in code or "SyntaxError" in code:
            return ExecutionOutput(
                success=False, stdout="", stderr="SyntaxError: unterminated string literal", exit_code=1, execution_time_ms=10
            )

        # Check timeout / infinite loop
        if "while True" in code:
            return ExecutionOutput(
                success=False, stdout="", stderr="Execution timed out after 5 seconds.", exit_code=124, execution_time_ms=5000
            )

        # If C++ compilation error
        if language == "cpp" and "COMPILE_FAIL" in code:
            return ExecutionOutput(
                success=False, stdout="", stderr="main.cpp:5:1: error: expected ';'", exit_code=1, execution_time_ms=30
            )

        # Execute python safely in-process for tests
        if language == "python":
            import io
            import sys

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            loc = {}
            try:
                exec(code, loc, loc)
                out = buf.getvalue()
                return ExecutionOutput(success=True, stdout=out, stderr="", exit_code=0, execution_time_ms=15)
            except Exception as exc:
                return ExecutionOutput(
                    success=False, stdout="", stderr=f"{type(exc).__name__}: {exc}", exit_code=1, execution_time_ms=15
                )
            finally:
                sys.stdout = old_stdout

        return ExecutionOutput(success=True, stdout=stdin, stderr="", exit_code=0, execution_time_ms=10)


@pytest.fixture
def orchestrator():
    return DebugOrchestrator(execution_service=SmartBenchmarkSandbox())


def test_benchmark_suite_has_10_problems():
    assert len(BenchmarkSuite.PROBLEMS) == 10
    names = [p.name for p in BenchmarkSuite.PROBLEMS]
    assert "Two Sum" in names
    assert "Valid Parentheses" in names
    assert "Binary Search" in names
    assert "Best Time to Buy and Sell Stock" in names
    assert "Maximum Subarray" in names
    assert "Contains Duplicate" in names
    assert "Valid Anagram" in names
    assert "Climbing Stairs" in names
    assert "Reverse Linked List" in names
    assert "Merge Intervals" in names


# CASE 1: SYNTAX ERROR
@pytest.mark.asyncio
async def test_case_1_syntax_error(orchestrator):
    req = DebugRequest(
        mode="general",
        language="python",
        code="def hello():\n    print('Unclosed\n",
    )
    report = await orchestrator.debug(req)
    assert report.failure_type in ("syntax", "compilation")
    assert report.status in ("fixed", "failed", "needs_review")
    assert report.validation.compile is not None


# CASE 2: RUNTIME ERROR
@pytest.mark.asyncio
async def test_case_2_runtime_error(orchestrator):
    py_code = """
numbers = [1, 2, 3]
for i in range(4):
    print(numbers[i])
"""
    req = DebugRequest(
        mode="general",
        language="python",
        code=py_code,
    )
    report = await orchestrator.debug(req)
    assert report.status in ("fixed", "failed", "needs_review")
    assert any("index" in e.likely_root_cause.lower() or "bounds" in e.likely_root_cause.lower() for e in report.evidence)


# CASE 3: LOGICAL ERROR (Actual != Expected)
@pytest.mark.asyncio
async def test_case_3_logical_error(orchestrator):
    p = BenchmarkSuite.get_problem("two_sum")
    assert p is not None
    req = DebugRequest(
        mode="leetcode",
        language="python",
        problem_statement=p.statement,
        constraints=p.constraints,
        code=p.buggy_code,
        test_cases=p.test_cases,
    )
    report = await orchestrator.debug(req)
    # The buggy code fails on [3,3] target 6, so evidence should show expected vs actual mismatch
    assert len(report.evidence) >= 1
    mismatch_ev = report.evidence[0]
    assert mismatch_ev.failure_type in ("edge_case_failure", "incorrect_output")
    assert mismatch_ev.expected_output is not None


# CASE 4: PERFORMANCE / COMPLEXITY ISSUE
def test_case_4_performance_complexity():
    quadratic_code = """
def twoSum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    res = CodeAnalysisEngine.analyze(
        code=quadratic_code,
        language="python",
        constraints=["1 <= nums.length <= 10^5"],
    )
    assert res.complexity.time_complexity in ("O(N²)", "O(N^2)")
    assert res.complexity.is_bottleneck is True
    assert "Time Limit Exceeded" in (res.complexity.warning or "")


# CASE 5: FIX VALIDATION (Buggy code fails -> Proposes fix -> Fix retested -> Passes)
@pytest.mark.asyncio
async def test_case_5_fix_validation(orchestrator):
    p = BenchmarkSuite.get_problem("two_sum")
    assert p is not None
    req = DebugRequest(
        mode="leetcode",
        language="python",
        problem_statement=p.statement,
        constraints=p.constraints,
        code=p.buggy_code,
        test_cases=p.test_cases,
    )
    report = await orchestrator.debug(req)
    assert report.status == "fixed"
    assert report.validation.tests is True
    assert report.tests_passed > 0
    assert report.diff != ""
