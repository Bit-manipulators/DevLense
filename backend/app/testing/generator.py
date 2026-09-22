from __future__ import annotations

from pydantic import BaseModel
from typing import Literal

from app.context.problem_context import ProblemContext
from app.testing.oracle import ExpectedResultEngine

TestSource = Literal["user", "problem_example", "generated"]
TestCategory = Literal["user", "example", "boundary", "edge", "stress"]


class TestCase(BaseModel):
    input_raw: str
    expected_output: str | None = None
    source: TestSource = "generated"
    category: TestCategory = "boundary"
    description: str = ""


class TestGenerationService:
    """Generates structured test cases derived from problem context, examples, and constraints."""

    _ARCHETYPE_BOUNDARY_TESTS: dict[str, list[tuple[str, str]]] = {
        "two sum": [
            ("nums = [3,3], target = 6", "Duplicates adding to target"),
            ("nums = [-1,-2,-3,-4,-5], target = -8", "Negative numbers"),
            ("nums = [0,4,3,0], target = 0", "Zeros in collection"),
            ("nums = [1,2,3,4,5,6], target = 11", "Extremes at the end"),
        ],
        "valid parentheses": [
            ('s = "([)]"', "Interleaved brackets (invalid)"),
            ('s = "{[]}"', "Properly nested different bracket types"),
            ('s = "["', "Single unclosed opening bracket"),
            ('s = "]"', "Single closing bracket without opening"),
            ('s = "((((((()))))))"', "Deeply nested valid brackets"),
        ],
        "binary search": [
            ("nums = [5], target = 5", "Single-element hit"),
            ("nums = [5], target = 2", "Single-element miss"),
            ("nums = [1,3,5,7,9], target = 1", "Target at index 0"),
            ("nums = [1,3,5,7,9], target = 9", "Target at last index"),
            ("nums = [1,3,5,7,9], target = 4", "Target absent inside range"),
        ],
        "best time to buy and sell stock": [
            ("prices = [7,6,4,3,1]", "Strictly decreasing prices (zero profit)"),
            ("prices = [1,2,3,4,5]", "Strictly increasing prices (max profit)"),
            ("prices = [2,4,1]", "Lowest day after high peak"),
            ("prices = [3,3,3,3]", "Flat / identical prices"),
        ],
        "maximum subarray": [
            ("nums = [-1]", "Single negative element"),
            ("nums = [-3,-2,-5,-1,-4]", "All negative numbers"),
            ("nums = [1,2,3,4]", "All positive numbers"),
            ("nums = [5,-2,3,-1,2]", "Alternating positive and negative"),
        ],
        "contains duplicate": [
            ("nums = [1,1]", "Two duplicate elements"),
            ("nums = [1,2,3,4]", "All unique elements"),
            ("nums = [1,5,-2,-4,0]", "No duplicates with negative values"),
        ],
        "valid anagram": [
            ('s = "a", t = "a"', "Single identical character"),
            ('s = "ab", t = "a"', "Mismatched length"),
            ('s = "rat", t = "car"', "Same length, different characters"),
            ('s = "aacc", t = "ccac"', "Same characters, different counts"),
        ],
        "climbing stairs": [
            ("n = 1", "Base case n = 1"),
            ("n = 2", "Base case n = 2"),
            ("n = 4", "Intermediate n = 4"),
            ("n = 5", "Intermediate n = 5"),
        ],
        "reverse linked list": [
            ("head = []", "Empty linked list"),
            ("head = [1]", "Single node"),
            ("head = [1,2]", "Two nodes"),
        ],
        "merge intervals": [
            ("intervals = [[1,4],[4,5]]", "Touching intervals at boundary"),
            ("intervals = [[1,4],[2,3]]", "Completely enclosed interval"),
            ("intervals = [[1,4],[5,6]]", "Completely disjoint intervals"),
        ],
        "fibonacci number": [
            ("n = 0", "Base case n = 0"),
            ("n = 1", "Base case n = 1"),
            ("n = 2", "Base case n = 2"),
            ("n = 5", "Intermediate n = 5"),
            ("n = 10", "Intermediate n = 10"),
        ],
        "array prototype last": [
            ("nums = [1, 2, 3]", "Non-empty array with elements"),
            ("nums = []", "Empty array edge case returning -1"),
            ("nums = [null]", "Array containing null"),
            ("nums = [0]", "Single zero element"),
        ],
    }

    @classmethod
    def generate_tests(
        cls,
        context: ProblemContext,
        max_tests: int = 10,
        user_test_cases: list[dict[str, str]] | None = None,
    ) -> list[TestCase]:
        tests: list[TestCase] = []
        seen_inputs: set[str] = set()

        # 1. User-provided test cases (highest priority)
        if user_test_cases:
            for tc in user_test_cases:
                inp = str(tc.get("input", "")).strip()
                if inp and inp not in seen_inputs:
                    seen_inputs.add(inp)
                    expected = tc.get("expected_output", tc.get("output"))
                    if not expected and context.problem_name:
                        expected = ExpectedResultEngine.resolve_expected(
                            input_raw=inp, problem_name=context.problem_name
                        )
                    tests.append(
                        TestCase(
                            input_raw=inp,
                            expected_output=expected,
                            source="user",
                            category="user",
                            description="User-supplied test case",
                        )
                    )

        # 2. Problem Examples
        for ex in context.examples:
            inp = ex.input_raw.strip()
            if inp and inp not in seen_inputs:
                seen_inputs.add(inp)
                expected = ex.output_raw.strip() if ex.output_raw else None
                if not expected and context.problem_name:
                    expected = ExpectedResultEngine.resolve_expected(
                        input_raw=inp, problem_name=context.problem_name
                    )
                tests.append(
                    TestCase(
                        input_raw=inp,
                        expected_output=expected,
                        source="problem_example",
                        category="example",
                        description="Example from problem statement",
                    )
                )

        # 3. Known archetype boundary cases
        if context.problem_name:
            p_name_lower = context.problem_name.lower()
            for key, boundary_cases in cls._ARCHETYPE_BOUNDARY_TESTS.items():
                if key in p_name_lower:
                    for inp, desc in boundary_cases:
                        if inp not in seen_inputs and len(tests) < max_tests:
                            seen_inputs.add(inp)
                            exp = ExpectedResultEngine.resolve_expected(
                                input_raw=inp, problem_name=context.problem_name
                            )
                            tests.append(
                                TestCase(
                                    input_raw=inp,
                                    expected_output=exp,
                                    source="generated",
                                    category="boundary",
                                    description=desc,
                                )
                            )

        # 4. General mode fallback boundary tests
        if not tests and context.mode == "general":
            general_cases = ["", "0", "1", "-1", "test"]
            for gc in general_cases:
                if len(tests) < max_tests:
                    tests.append(
                        TestCase(
                            input_raw=gc,
                            expected_output=None,
                            source="generated",
                            category="edge",
                            description="General boundary input",
                        )
                    )

        return tests[:max_tests]
