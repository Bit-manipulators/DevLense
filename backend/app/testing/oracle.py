from __future__ import annotations

import ast
import json
import re
from typing import Any, Callable


class ExpectedResultEngine:
    """Deterministically resolves expected test outputs via user inputs, examples, and reference implementations."""

    @classmethod
    def resolve_expected(
        cls,
        *,
        input_raw: str,
        problem_name: str | None = None,
        user_expected: str | None = None,
    ) -> str | None:
        # Priority 1: User-provided expected result
        if user_expected is not None and str(user_expected).strip():
            return str(user_expected).strip()

        # Priority 2: Archetype reference implementation
        if problem_name:
            ref_output = cls._run_reference(problem_name, input_raw)
            if ref_output is not None:
                return ref_output

        # Priority 3: State explicitly that expected output cannot be automatically determined
        return None

    @classmethod
    def _run_reference(cls, problem_name: str, input_raw: str) -> str | None:
        p_name = problem_name.lower().strip()
        ref_fn: Callable[..., Any] | None = None

        if "two sum" in p_name:
            ref_fn = cls._ref_two_sum
        elif "valid parentheses" in p_name:
            ref_fn = cls._ref_valid_parentheses
        elif "binary search" in p_name:
            ref_fn = cls._ref_binary_search
        elif "stock" in p_name:
            ref_fn = cls._ref_max_profit
        elif "maximum subarray" in p_name or "max subarray" in p_name:
            ref_fn = cls._ref_max_subarray
        elif "contains duplicate" in p_name:
            ref_fn = cls._ref_contains_duplicate
        elif "valid anagram" in p_name:
            ref_fn = cls._ref_is_anagram
        elif "climbing stairs" in p_name:
            ref_fn = cls._ref_climb_stairs
        elif "fibonacci" in p_name:
            ref_fn = cls._ref_fibonacci
        elif "merge intervals" in p_name:
            ref_fn = cls._ref_merge_intervals
        elif "reverse linked list" in p_name:
            ref_fn = cls._ref_reverse_linked_list
        elif "array prototype last" in p_name:
            ref_fn = cls._ref_array_last

        if not ref_fn:
            return None



        try:
            parsed_args = cls._parse_inputs(input_raw)
            res = ref_fn(*parsed_args)
            if isinstance(res, bool):
                return "true" if res else "false"
            return json.dumps(res, separators=(",", ""))
        except Exception:
            return None

    @classmethod
    def _parse_inputs(cls, input_raw: str) -> list[Any]:
        # Handle formats like "nums = [2,7,11,15], target = 9" or "[2,7,11,15], 9"
        cleaned = input_raw.strip()
        # Remove variable names like "nums =", "target =", "s =", "prices ="
        cleaned_no_vars = re.sub(r"\b[a-zA-Z_]\w*\s*=\s*", "", cleaned)

        # Wrap in tuple and parse with ast.literal_eval
        try:
            val = ast.literal_eval(f"({cleaned_no_vars})")
            if isinstance(val, tuple):
                return list(val)
            return [val]
        except Exception:
            pass

        # Try parsing single JSON
        try:
            val = json.loads(cleaned)
            return [val]
        except Exception:
            pass

        return [cleaned]

    # --- Reference Implementations ---

    @staticmethod
    def _ref_two_sum(nums: list[int], target: int) -> list[int]:
        lookup: dict[int, int] = {}
        for idx, num in enumerate(nums):
            complement = target - num
            if complement in lookup:
                return [lookup[complement], idx]
            lookup[num] = idx
        return []

    @staticmethod
    def _ref_valid_parentheses(s: str) -> bool:
        mapping = {")": "(", "}": "{", "]": "["}
        stack: list[str] = []
        for char in str(s):
            if char in mapping:
                top_element = stack.pop() if stack else "#"
                if mapping[char] != top_element:
                    return False
            else:
                stack.append(char)
        return not stack

    @staticmethod
    def _ref_binary_search(nums: list[int], target: int) -> int:
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1

    @staticmethod
    def _ref_max_profit(prices: list[int]) -> int:
        if not prices:
            return 0
        min_price = float("inf")
        max_profit = 0
        for price in prices:
            if price < min_price:
                min_price = price
            elif price - min_price > max_profit:
                max_profit = price - min_price
        return int(max_profit)

    @staticmethod
    def _ref_max_subarray(nums: list[int]) -> int:
        if not nums:
            return 0
        current_sum = max_sum = nums[0]
        for x in nums[1:]:
            current_sum = max(x, current_sum + x)
            max_sum = max(max_sum, current_sum)
        return max_sum

    @staticmethod
    def _ref_contains_duplicate(nums: list[int]) -> bool:
        seen = set()
        for num in nums:
            if num in seen:
                return True
            seen.add(num)
        return False

    @staticmethod
    def _ref_is_anagram(s: str, t: str) -> bool:
        return sorted(str(s)) == sorted(str(t))

    @staticmethod
    def _ref_climb_stairs(n: int) -> int:
        n = int(n)
        if n <= 2:
            return n
        first, second = 1, 2
        for _ in range(3, n + 1):
            first, second = second, first + second
        return second

    @staticmethod
    def _ref_fibonacci(n: int) -> int:
        n = int(n)
        if n <= 1:
            return n
        first, second = 0, 1
        for _ in range(2, n + 1):
            first, second = second, first + second
        return second


    @staticmethod
    def _ref_merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
        if not intervals:
            return []
        intervals.sort(key=lambda x: x[0])
        merged: list[list[int]] = [intervals[0]]
        for current in intervals[1:]:
            prev = merged[-1]
            if current[0] <= prev[1]:
                prev[1] = max(prev[1], current[1])
            else:
                merged.append(current)
        return merged

    @staticmethod
    def _ref_reverse_linked_list(head: list[int]) -> list[int]:
        if not isinstance(head, list):
            return []
        return head[::-1]

    @staticmethod
    def _ref_array_last(nums: Any = None) -> Any:
        if isinstance(nums, list):
            return nums[-1] if nums else -1
        return -1

