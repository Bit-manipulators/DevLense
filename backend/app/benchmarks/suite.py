from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BenchmarkProblem:
    id: str
    name: str
    language: str
    statement: str
    constraints: str
    buggy_code: str
    fixed_code: str
    expected_failure_type: str
    test_cases: list[dict[str, str]] = field(default_factory=list)


class BenchmarkSuite:
    """Canonical 10-problem benchmark suite for evaluating DevLens debugging engine."""

    PROBLEMS: list[BenchmarkProblem] = [
        # 1. Two Sum
        BenchmarkProblem(
            id="two_sum",
            name="Two Sum",
            language="python",
            statement="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
            constraints="2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9",
            buggy_code=(
                "def twoSum(nums, target):\n"
                "    # Bug: duplicate numbers overwrite index before check, failing on [3,3] target 6\n"
                "    seen = {}\n"
                "    for i, num in enumerate(nums):\n"
                "        seen[num] = i\n"
                "        diff = target - num\n"
                "        if diff in seen and seen[diff] != i:\n"
                "            return [seen[diff], i]\n"
                "    return []\n"
            ),
            fixed_code=(
                "def twoSum(nums, target):\n"
                "    seen = {}\n"
                "    for i, num in enumerate(nums):\n"
                "        diff = target - num\n"
                "        if diff in seen:\n"
                "            return [seen[diff], i]\n"
                "        seen[num] = i\n"
                "    return []\n"
            ),
            expected_failure_type="edge_case_failure",
            test_cases=[
                {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"},
                {"input": "nums = [3,3], target = 6", "output": "[0,1]"},
                {"input": "nums = [3,2,4], target = 6", "output": "[1,2]"},
            ],
        ),
        # 2. Valid Parentheses
        BenchmarkProblem(
            id="valid_parentheses",
            name="Valid Parentheses",
            language="python",
            statement="Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.",
            constraints="1 <= s.length <= 10^4",
            buggy_code=(
                "def isValid(s):\n"
                "    # Bug: does not check stack emptiness at end\n"
                "    stack = []\n"
                "    mapping = {')': '(', '}': '{', ']': '['}\n"
                "    for char in s:\n"
                "        if char in mapping:\n"
                "            if not stack or stack.pop() != mapping[char]:\n"
                "                return False\n"
                "        else:\n"
                "            stack.append(char)\n"
                "    return True # Bug! Should be len(stack) == 0\n"
            ),
            fixed_code=(
                "def isValid(s):\n"
                "    stack = []\n"
                "    mapping = {')': '(', '}': '{', ']': '['}\n"
                "    for char in s:\n"
                "        if char in mapping:\n"
                "            if not stack or stack.pop() != mapping[char]:\n"
                "                return False\n"
                "        else:\n"
                "            stack.append(char)\n"
                "    return len(stack) == 0\n"
            ),
            expected_failure_type="incorrect_output",
            test_cases=[
                {"input": 's = "()"', "output": "true"},
                {"input": 's = "([)]"', "output": "false"},
                {"input": 's = "["', "output": "false"},
            ],
        ),
        # 3. Binary Search
        BenchmarkProblem(
            id="binary_search",
            name="Binary Search",
            language="python",
            statement="Given an array of integers nums sorted in ascending order, and an integer target, write a function to search target in nums.",
            constraints="1 <= nums.length <= 10^4\n-10^4 < nums[i], target < 10^4",
            buggy_code=(
                "def search(nums, target):\n"
                "    # Bug: strict '<' skips single-element and boundary comparisons\n"
                "    left, right = 0, len(nums) - 1\n"
                "    while left < right:\n"
                "        mid = (left + right) // 2\n"
                "        if nums[mid] == target:\n"
                "            return mid\n"
                "        elif nums[mid] < target:\n"
                "            left = mid + 1\n"
                "        else:\n"
                "            right = mid - 1\n"
                "    return -1\n"
            ),
            fixed_code=(
                "def search(nums, target):\n"
                "    left, right = 0, len(nums) - 1\n"
                "    while left <= right:\n"
                "        mid = (left + right) // 2\n"
                "        if nums[mid] == target:\n"
                "            return mid\n"
                "        elif nums[mid] < target:\n"
                "            left = mid + 1\n"
                "        else:\n"
                "            right = mid - 1\n"
                "    return -1\n"
            ),
            expected_failure_type="edge_case_failure",
            test_cases=[
                {"input": "nums = [5], target = 5", "output": "0"},
                {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"},
                {"input": "nums = [-1,0,3,5,9,12], target = 2", "output": "-1"},
            ],
        ),
        # 4. Best Time to Buy and Sell Stock
        BenchmarkProblem(
            id="buy_sell_stock",
            name="Best Time to Buy and Sell Stock",
            language="python",
            statement="Find the maximum profit you can achieve from buying and selling stock once.",
            constraints="1 <= prices.length <= 10^5\n0 <= prices[i] <= 10^4",
            buggy_code=(
                "def maxProfit(prices):\n"
                "    # Bug: returns negative if prices only decrease\n"
                "    min_price = prices[0]\n"
                "    max_profit = -9999\n"
                "    for price in prices:\n"
                "        if price < min_price:\n"
                "            min_price = price\n"
                "        elif price - min_price > max_profit:\n"
                "            max_profit = price - min_price\n"
                "    return max_profit\n"
            ),
            fixed_code=(
                "def maxProfit(prices):\n"
                "    if not prices:\n"
                "        return 0\n"
                "    min_price = float('inf')\n"
                "    max_profit = 0\n"
                "    for price in prices:\n"
                "        if price < min_price:\n"
                "            min_price = price\n"
                "        elif price - min_price > max_profit:\n"
                "            max_profit = price - min_price\n"
                "    return max_profit\n"
            ),
            expected_failure_type="edge_case_failure",
            test_cases=[
                {"input": "prices = [7,1,5,3,6,4]", "output": "5"},
                {"input": "prices = [7,6,4,3,1]", "output": "0"},
            ],
        ),
        # 5. Maximum Subarray
        BenchmarkProblem(
            id="maximum_subarray",
            name="Maximum Subarray",
            language="python",
            statement="Given an integer array nums, find the subarray with the largest sum, and return its sum.",
            constraints="1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4",
            buggy_code=(
                "def maxSubArray(nums):\n"
                "    # Bug: initializes max_sum to 0, failing on all-negative arrays\n"
                "    current_sum = 0\n"
                "    max_sum = 0\n"
                "    for x in nums:\n"
                "        current_sum = max(x, current_sum + x)\n"
                "        max_sum = max(max_sum, current_sum)\n"
                "    return max_sum\n"
            ),
            fixed_code=(
                "def maxSubArray(nums):\n"
                "    if not nums:\n"
                "        return 0\n"
                "    current_sum = max_sum = nums[0]\n"
                "    for x in nums[1:]:\n"
                "        current_sum = max(x, current_sum + x)\n"
                "        max_sum = max(max_sum, current_sum)\n"
                "    return max_sum\n"
            ),
            expected_failure_type="edge_case_failure",
            test_cases=[
                {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6"},
                {"input": "nums = [-1]", "output": "-1"},
                {"input": "nums = [-3,-2,-5]", "output": "-2"},
            ],
        ),
        # 6. Contains Duplicate
        BenchmarkProblem(
            id="contains_duplicate",
            name="Contains Duplicate",
            language="python",
            statement="Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.",
            constraints="1 <= nums.length <= 10^5",
            buggy_code=(
                "def containsDuplicate(nums):\n"
                "    # Bug: returns True only if consecutive duplicates exist\n"
                "    for i in range(len(nums) - 1):\n"
                "        if nums[i] == nums[i + 1]:\n"
                "            return True\n"
                "    return False\n"
            ),
            fixed_code=(
                "def containsDuplicate(nums):\n"
                "    return len(nums) != len(set(nums))\n"
            ),
            expected_failure_type="incorrect_output",
            test_cases=[
                {"input": "nums = [1,2,3,1]", "output": "true"},
                {"input": "nums = [1,2,3,4]", "output": "false"},
            ],
        ),
        # 7. Valid Anagram
        BenchmarkProblem(
            id="valid_anagram",
            name="Valid Anagram",
            language="python",
            statement="Given two strings s and t, return true if t is an anagram of s, and false otherwise.",
            constraints="1 <= s.length, t.length <= 5 * 10^4",
            buggy_code=(
                "def isAnagram(s, t):\n"
                "    # Bug: only checks set of characters, ignoring character counts\n"
                "    return set(s) == set(t)\n"
            ),
            fixed_code=(
                "def isAnagram(s, t):\n"
                "    return sorted(s) == sorted(t)\n"
            ),
            expected_failure_type="incorrect_output",
            test_cases=[
                {"input": 's = "anagram", t = "nagaram"', "output": "true"},
                {"input": 's = "rat", t = "car"', "output": "false"},
                {"input": 's = "aacc", t = "ccac"', "output": "false"},
            ],
        ),
        # 8. Climbing Stairs
        BenchmarkProblem(
            id="climbing_stairs",
            name="Climbing Stairs",
            language="python",
            statement="You are climbing a staircase. It takes n steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
            constraints="1 <= n <= 45",
            buggy_code=(
                "def climbStairs(n):\n"
                "    # Bug: wrong base case for n=1\n"
                "    if n == 1:\n"
                "        return 0\n"
                "    a, b = 1, 2\n"
                "    for _ in range(3, n + 1):\n"
                "        a, b = b, a + b\n"
                "    return b\n"
            ),
            fixed_code=(
                "def climbStairs(n):\n"
                "    if n <= 2:\n"
                "        return n\n"
                "    a, b = 1, 2\n"
                "    for _ in range(3, n + 1):\n"
                "        a, b = b, a + b\n"
                "    return b\n"
            ),
            expected_failure_type="edge_case_failure",
            test_cases=[
                {"input": "n = 1", "output": "1"},
                {"input": "n = 2", "output": "2"},
                {"input": "n = 3", "output": "3"},
            ],
        ),
        # 9. Reverse Linked List
        BenchmarkProblem(
            id="reverse_linked_list",
            name="Reverse Linked List",
            language="python",
            statement="Given the head of a singly linked list, reverse the list, and return the reversed list.",
            constraints="0 <= Number of nodes <= 5000",
            buggy_code=(
                "def reverseList(head):\n"
                "    # Bug: crashes on empty list\n"
                "    return head[::-1] if len(head) > 0 else None\n"
            ),
            fixed_code=(
                "def reverseList(head):\n"
                "    return head[::-1] if isinstance(head, list) else []\n"
            ),
            expected_failure_type="edge_case_failure",
            test_cases=[
                {"input": "head = [1,2,3,4,5]", "output": "[5,4,3,2,1]"},
                {"input": "head = []", "output": "[]"},
            ],
        ),
        # 10. Merge Intervals
        BenchmarkProblem(
            id="merge_intervals",
            name="Merge Intervals",
            language="python",
            statement="Given an array of intervals where intervals[i] = [starti, endi], merge all overlapping intervals.",
            constraints="1 <= intervals.length <= 10^4",
            buggy_code=(
                "def merge(intervals):\n"
                "    # Bug: assumes input is already sorted, fails on unsorted intervals\n"
                "    merged = [intervals[0]]\n"
                "    for current in intervals[1:]:\n"
                "        prev = merged[-1]\n"
                "        if current[0] <= prev[1]:\n"
                "            prev[1] = max(prev[1], current[1])\n"
                "        else:\n"
                "            merged.append(current)\n"
                "    return merged\n"
            ),
            fixed_code=(
                "def merge(intervals):\n"
                "    if not intervals:\n"
                "        return []\n"
                "    intervals.sort(key=lambda x: x[0])\n"
                "    merged = [intervals[0]]\n"
                "    for current in intervals[1:]:\n"
                "        prev = merged[-1]\n"
                "        if current[0] <= prev[1]:\n"
                "            prev[1] = max(prev[1], current[1])\n"
                "        else:\n"
                "            merged.append(current)\n"
                "    return merged\n"
            ),
            expected_failure_type="incorrect_output",
            test_cases=[
                {"input": "intervals = [[1,3],[2,6],[8,10],[15,18]]", "output": "[[1,6],[8,10],[15,18]]"},
                {"input": "intervals = [[1,4],[0,4]]", "output": "[[0,4]]"},
            ],
        ),
    ]

    @classmethod
    def get_problem(cls, problem_id: str) -> BenchmarkProblem | None:
        for p in cls.PROBLEMS:
            if p.id == problem_id or p.name.lower() == problem_id.lower():
                return p
        return None
