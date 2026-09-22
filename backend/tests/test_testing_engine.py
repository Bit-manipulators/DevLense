from __future__ import annotations

from app.context.problem_understanding import ProblemUnderstandingService
from app.testing.comparator import OutputComparator
from app.testing.generator import TestGenerationService
from app.testing.oracle import ExpectedResultEngine


def test_expected_result_engine_two_sum():
    res = ExpectedResultEngine.resolve_expected(
        input_raw="nums = [3,3], target = 6", problem_name="Two Sum"
    )
    assert res == "[0,1]"

    res2 = ExpectedResultEngine.resolve_expected(
        input_raw="nums = [2,7,11,15], target = 9", problem_name="Two Sum"
    )
    assert res2 == "[0,1]"


def test_output_comparator():
    # Exact and whitespace
    match, _ = OutputComparator.compare("[0, 1]", "[0,1]")
    assert match is True

    # Boolean case-insensitivity
    match, _ = OutputComparator.compare("true", "True")
    assert match is True

    # Permutation match for two sum pairs
    match, _ = OutputComparator.compare("[0, 1]", "[1, 0]")
    assert match is True

    # Failure case
    match, msg = OutputComparator.compare("[0, 1]", "[]")
    assert match is False
    assert "Expected '[0, 1]'" in msg


def test_test_generation_service_two_sum():
    service = ProblemUnderstandingService()
    ctx = service.analyze(
        problem_statement="Two Sum: Given an array of integers nums and an integer target, return indices...",
        constraints="2 <= nums.length <= 10^4",
        language="python",
        mode="leetcode",
    )
    tests = TestGenerationService.generate_tests(ctx, max_tests=5)
    assert len(tests) >= 3
    assert any("3,3" in t.input_raw for t in tests)
    # Check that expected output was resolved deterministically
    dup_test = next(t for t in tests if "3,3" in t.input_raw)
    assert dup_test.expected_output == "[0,1]"
