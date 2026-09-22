from __future__ import annotations

from app.context.problem_understanding import ProblemUnderstandingService


def test_problem_understanding_two_sum():
    service = ProblemUnderstandingService()
    statement = """
    Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.
    You may assume that each input would have exactly one solution, and you may not use the same element twice.

    Example 1:
    Input: nums = [2,7,11,15], target = 9
    Output: [0,1]
    Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

    Constraints:
    2 <= nums.length <= 10^4
    -10^9 <= nums[i] <= 10^9
    -10^9 <= target <= 10^9
    """
    code = "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i + 1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n"

    ctx = service.analyze(
        problem_statement=statement,
        constraints="2 <= nums.length <= 10^4",
        code=code,
        language="python",
        mode="leetcode",
    )

    assert ctx.problem_name == "Two Sum"
    assert "indices of two numbers" in ctx.objective.lower() or "two numbers" in ctx.objective.lower()
    assert len(ctx.examples) >= 1
    assert "nums = [2,7,11,15]" in ctx.examples[0].input_raw
    assert ctx.examples[0].output_raw == "[0,1]"
    assert len(ctx.edge_cases) >= 2
    assert ctx.expected_complexity["time"] == "O(N)"
    assert ctx.function_signature is not None
    assert "twoSum" in ctx.function_signature


def test_problem_understanding_general_mode():
    service = ProblemUnderstandingService()
    statement = "Fix IndexError in array processing."
    code = "arr = [1, 2, 3]\nfor i in range(4):\n    print(arr[i])\n"

    ctx = service.analyze(
        problem_statement=statement,
        code=code,
        language="python",
        mode="general",
    )

    assert ctx.mode == "general"
    assert ctx.language == "python"
    assert "IndexError" in ctx.objective or "array processing" in ctx.objective
