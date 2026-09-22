from __future__ import annotations

import re
from typing import Any

from app.context.problem_context import ProblemContext, ProblemExample
from app.languages.registry import LanguageRegistry


class ProblemUnderstandingService:
    """Extracts objectives, constraints, signatures, examples, and algorithmic properties."""

    _KNOWN_ARCHETYPES: dict[str, dict[str, Any]] = {
        "two sum": {
            "name": "Two Sum",
            "objective": "Find indices of two numbers that add up to a target sum.",
            "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "Exactly one valid answer exists."],
            "expected_complexity": {"time": "O(N)", "space": "O(N)"},
            "edge_cases": [
                "Two identical numbers that add to target (e.g., nums=[3,3], target=6)",
                "Negative numbers in nums (e.g., nums=[-1,-2,-3,-4,-5], target=-8)",
                "Target is zero with positive and negative elements",
                "Solution at the extreme ends of the array (first and last indices)",
            ],
            "sample_examples": [
                ProblemExample(input_raw="nums = [2,7,11,15], target = 9", output_raw="[0,1]"),
                ProblemExample(input_raw="nums = [3,2,4], target = 6", output_raw="[1,2]"),
                ProblemExample(input_raw="nums = [3,3], target = 6", output_raw="[0,1]"),
            ],
        },
        "valid parentheses": {
            "name": "Valid Parentheses",
            "objective": "Determine if the input string containing brackets '()[]{}' is valid.",
            "constraints": ["1 <= s.length <= 10^4", "s consists of parentheses only '()[]{}'."],
            "expected_complexity": {"time": "O(N)", "space": "O(N)"},
            "edge_cases": [
                "Empty string or single character (e.g., '(' or ']')",
                "Odd length string cannot be valid",
                "Mismatched bracket types (e.g., '(]')",
                "Wrong nesting order (e.g., '([)]')",
                "All closing brackets or all opening brackets",
            ],
            "sample_examples": [
                ProblemExample(input_raw='s = "()"', output_raw="true"),
                ProblemExample(input_raw='s = "()[]{}"', output_raw="true"),
                ProblemExample(input_raw='s = "(]"', output_raw="false"),
            ],
        },
        "binary search": {
            "name": "Binary Search",
            "objective": "Search for target in sorted array nums in O(log n) runtime.",
            "constraints": ["1 <= nums.length <= 10^4", "-10^4 < nums[i], target < 10^4", "nums is sorted in ascending order."],
            "expected_complexity": {"time": "O(log N)", "space": "O(1)"},
            "edge_cases": [
                "Target at index 0 (first element)",
                "Target at index len-1 (last element)",
                "Target not present (smaller than min or greater than max)",
                "Single-element array [1], target 1 -> 0",
                "Single-element array [1], target 2 -> -1",
            ],
            "sample_examples": [
                ProblemExample(input_raw="nums = [-1,0,3,5,9,12], target = 9", output_raw="4"),
                ProblemExample(input_raw="nums = [-1,0,3,5,9,12], target = 2", output_raw="-1"),
            ],
        },
        "best time to buy and sell stock": {
            "name": "Best Time to Buy and Sell Stock",
            "objective": "Maximize profit by choosing a single day to buy one stock and choosing a different day in the future to sell it.",
            "constraints": ["1 <= prices.length <= 10^5", "0 <= prices[i] <= 10^4"],
            "expected_complexity": {"time": "O(N)", "space": "O(1)"},
            "edge_cases": [
                "Strictly decreasing prices (e.g., [7,6,4,3,1] -> profit 0)",
                "Strictly increasing prices (e.g., [1,2,3,4,5] -> buy at first, sell at last)",
                "Single-day prices [5] -> profit 0",
                "All identical prices [3,3,3,3] -> profit 0",
            ],
            "sample_examples": [
                ProblemExample(input_raw="prices = [7,1,5,3,6,4]", output_raw="5"),
                ProblemExample(input_raw="prices = [7,6,4,3,1]", output_raw="0"),
            ],
        },
        "maximum subarray": {
            "name": "Maximum Subarray",
            "objective": "Find the subarray with the largest sum and return its sum.",
            "constraints": ["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
            "expected_complexity": {"time": "O(N)", "space": "O(1)"},
            "edge_cases": [
                "All negative numbers (e.g., [-3, -1, -5] -> max is -1)",
                "Single-element array [5] -> 5",
                "All positive numbers (sum of entire array)",
                "Alternating large positive and negative numbers",
            ],
            "sample_examples": [
                ProblemExample(input_raw="nums = [-2,1,-3,4,-1,2,1,-5,4]", output_raw="6"),
                ProblemExample(input_raw="nums = [1]", output_raw="1"),
                ProblemExample(input_raw="nums = [5,4,-1,7,8]", output_raw="23"),
            ],
        },
        "contains duplicate": {
            "name": "Contains Duplicate",
            "objective": "Return true if any value appears at least twice in the array, and false if every element is distinct.",
            "constraints": ["1 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
            "expected_complexity": {"time": "O(N)", "space": "O(N)"},
            "edge_cases": [
                "Single element [1] -> false",
                "All duplicates [2,2,2,2] -> true",
                "Duplicate at extreme ends [1,2,3,4,1] -> true",
                "All unique elements [1,2,3,4,5] -> false",
            ],
            "sample_examples": [
                ProblemExample(input_raw="nums = [1,2,3,1]", output_raw="true"),
                ProblemExample(input_raw="nums = [1,2,3,4]", output_raw="false"),
                ProblemExample(input_raw="nums = [1,1,1,3,3,4,3,2,4,2]", output_raw="true"),
            ],
        },
        "valid anagram": {
            "name": "Valid Anagram",
            "objective": "Given two strings s and t, return true if t is an anagram of s, and false otherwise.",
            "constraints": ["1 <= s.length, t.length <= 5 * 10^4", "s and t consist of lowercase English letters."],
            "expected_complexity": {"time": "O(N)", "space": "O(1)"},
            "edge_cases": [
                "Different lengths (immediately false)",
                "Single identical characters (e.g. s='a', t='a' -> true)",
                "Identical strings",
                "Same characters but different frequency counts",
            ],
            "sample_examples": [
                ProblemExample(input_raw='s = "anagram", t = "nagaram"', output_raw="true"),
                ProblemExample(input_raw='s = "rat", t = "car"', output_raw="false"),
            ],
        },
        "climbing stairs": {
            "name": "Climbing Stairs",
            "objective": "Determine how many distinct ways you can climb n stairs taking 1 or 2 steps each time.",
            "constraints": ["1 <= n <= 45"],
            "expected_complexity": {"time": "O(N)", "space": "O(1)"},
            "edge_cases": [
                "n = 1 -> 1 way",
                "n = 2 -> 2 ways",
                "n = 3 -> 3 ways",
                "Upper bound n = 45",
            ],
            "sample_examples": [
                ProblemExample(input_raw="n = 2", output_raw="2"),
                ProblemExample(input_raw="n = 3", output_raw="3"),
            ],
        },
        "reverse linked list": {
            "name": "Reverse Linked List",
            "objective": "Reverse a singly linked list and return the reversed list head.",
            "constraints": ["The number of nodes in the list is in the range [0, 5000].", "-5000 <= Node.val <= 5000"],
            "expected_complexity": {"time": "O(N)", "space": "O(1)"},
            "edge_cases": [
                "Empty list (head = null or [])",
                "Single-node list [1]",
                "Two-node list [1,2]",
            ],
            "sample_examples": [
                ProblemExample(input_raw="head = [1,2,3,4,5]", output_raw="[5,4,3,2,1]"),
                ProblemExample(input_raw="head = [1,2]", output_raw="[2,1]"),
                ProblemExample(input_raw="head = []", output_raw="[]"),
            ],
        },
        "merge intervals": {
            "name": "Merge Intervals",
            "objective": "Merge all overlapping intervals and return an array of the non-overlapping intervals.",
            "constraints": ["1 <= intervals.length <= 10^4", "intervals[i].length == 2", "0 <= start <= end <= 10^4"],
            "expected_complexity": {"time": "O(N log N)", "space": "O(N)"},
            "edge_cases": [
                "Single interval [[1,4]] -> [[1,4]]",
                "No overlapping intervals [[1,2],[3,4]] -> [[1,2],[3,4]]",
                "One interval completely inside another [[1,10],[2,5]] -> [[1,10]]",
                "Unsorted intervals [[3,4],[1,2]]",
                "Touching boundaries [[1,4],[4,5]] -> [[1,5]]",
            ],
            "sample_examples": [
                ProblemExample(input_raw="intervals = [[1,3],[2,6],[8,10],[15,18]]", output_raw="[[1,6],[8,10],[15,18]]"),
                ProblemExample(input_raw="intervals = [[1,4],[4,5]]", output_raw="[[1,5]]"),
            ],
        },
        "fibonacci number": {
            "name": "Fibonacci Number",
            "objective": "Calculate the n-th Fibonacci number where F(0)=0, F(1)=1, and F(n)=F(n-1)+F(n-2).",
            "constraints": ["0 <= n <= 30"],
            "expected_complexity": {"time": "O(N)", "space": "O(1)"},
            "edge_cases": [
                "n = 0 -> 0",
                "n = 1 -> 1",
                "n = 2 -> 1",
                "n = 30 -> 832040",
            ],
            "sample_examples": [
                ProblemExample(input_raw="n = 2", output_raw="1"),
                ProblemExample(input_raw="n = 3", output_raw="2"),
                ProblemExample(input_raw="n = 4", output_raw="3"),
            ],
        },
        "array prototype last": {
            "name": "Array Prototype Last",
            "objective": "Enhance all arrays such that array.last() returns the last element, or -1 if empty.",
            "constraints": ["0 <= arr.length <= 1000"],
            "expected_complexity": {"time": "O(1)", "space": "O(1)"},
            "edge_cases": [
                "Empty array [] -> -1",
                "Single element [1] -> 1",
                "Multiple elements [1, 2, 3] -> 3",
            ],
            "sample_examples": [
                ProblemExample(input_raw="nums = [1, 2, 3]", output_raw="3"),
                ProblemExample(input_raw="nums = []", output_raw="-1"),
            ],
        },
    }


    def analyze(
        self,
        *,
        problem_statement: str = "",
        constraints: str = "",
        code: str = "",
        language: str = "python",
        mode: str = "general",
        user_test_cases: list[dict[str, Any]] | None = None,
    ) -> ProblemContext:
        canonical_lang = LanguageRegistry.normalize(language)
        statement = problem_statement.strip()
        raw_constraints = constraints.strip()

        # 1. Check for standard LeetCode archetype matches against statement and code
        matched_archetype = self._match_archetype(statement, code)

        # 2. Extract objective
        objective = self._extract_objective(statement, matched_archetype)

        # 3. Extract constraints
        parsed_constraints = self._extract_constraints(raw_constraints, statement, matched_archetype)

        # 4. Extract examples
        examples = self._extract_examples(statement, user_test_cases, matched_archetype)

        # 5. Extract function signature from code or statement
        sig = self._extract_signature(code, statement, canonical_lang)

        # 6. Extract/Infer edge cases
        edge_cases = self._infer_edge_cases(parsed_constraints, matched_archetype)

        # 7. Infer expected complexity from constraints
        expected_complexity = self._infer_expected_complexity(parsed_constraints, matched_archetype)

        problem_name = matched_archetype["name"] if matched_archetype else None

        return ProblemContext(
            mode=mode,
            objective=objective,
            input_description=self._extract_input_description(statement, examples),
            output_description=self._extract_output_description(statement, examples),
            constraints=parsed_constraints,
            examples=examples,
            edge_cases=edge_cases,
            function_signature=sig,
            expected_complexity=expected_complexity,
            language=canonical_lang,
            raw_statement=statement,
            raw_constraints=raw_constraints,
            problem_name=problem_name,
        )

    def _match_archetype(self, text: str, code: str = "") -> dict[str, Any] | None:
        combined = (text + " " + code).lower()
        if not combined.strip():
            return None
        for key, archetype in self._KNOWN_ARCHETYPES.items():
            if key in combined:
                return archetype
            # Check for strong keyword and function name patterns
            if key == "two sum" and ("twosum" in combined or ("target" in combined and ("indices" in combined or "two numbers" in combined))):
                return archetype
            if key == "valid parentheses" and ("isvalid" in combined or "parentheses" in combined or ("bracket" in combined and "valid" in combined)):
                return archetype
            if key == "fibonacci number" and ("fib(" in combined or "fibonacci" in combined or "fib =" in combined):
                return archetype
            if key == "best time to buy and sell stock" and ("maxprofit" in combined or ("buy" in combined and "sell" in combined)):
                return archetype
            if key == "maximum subarray" and ("maxsubarray" in combined or "kadane" in combined or ("contiguous" in combined and "largest sum" in combined)):
                return archetype
            if key == "binary search" and ("binarysearch" in combined or ("sorted" in combined and "search" in combined)):
                return archetype
            if key == "contains duplicate" and ("containsduplicate" in combined or ("duplicate" in combined and "distinct" in combined)):
                return archetype
            if key == "climbing stairs" and ("climbstairs" in combined or ("climb" in combined and "stairs" in combined)):
                return archetype
            if key == "merge intervals" and ("mergeintervals" in combined or ("merge" in combined and "intervals" in combined)):
                return archetype
            if key == "reverse linked list" and ("reverselist" in combined or ("reverse" in combined and "linked list" in combined)):
                return archetype
            if key == "valid anagram" and ("isanagram" in combined or "anagram" in combined):
                return archetype
            if key == "array prototype last" and ("array.prototype.last" in combined or "prototype.last" in combined):
                return archetype
        return None



    def _extract_objective(self, statement: str, archetype: dict[str, Any] | None) -> str:
        if archetype and archetype.get("objective"):
            return archetype["objective"]
        if not statement:
            return "General Code Debugging"
        # Take the first non-empty paragraph or sentence
        lines = [line.strip() for line in statement.splitlines() if line.strip()]
        if lines:
            first_line = lines[0]
            if len(first_line) > 200:
                first_sentence = first_line.split(". ")[0]
                return first_sentence + ("." if not first_sentence.endswith(".") else "")
            return first_line
        return "Debug and verify the provided code implementation."

    def _extract_constraints(
        self, raw_constraints: str, statement: str, archetype: dict[str, Any] | None
    ) -> list[str]:
        results: list[str] = []
        source_text = f"{raw_constraints}\n{statement}"

        # Match bullet points, equations, bounds
        constraint_patterns = [
            r"(?:^|\n)\s*[-*•]\s*(.+?)(?=\n\s*[-*•]|\n\n|$)",
            r"(\d+\s*<=\s*[\w.\[\]]+\s*<=\s*[\d^]+)",
            r"([\w.\[\]]+\.length\s*<=\s*[\d^]+)",
            r"([0-9\^]+\s*<=\s*[\w.\[\]]+)",
            r"(-?[\d^]+\s*<=\s*[\w.\[\]]+\s*<=\s*[\d^]+)",
        ]

        if raw_constraints:
            for line in raw_constraints.splitlines():
                clean = line.strip().lstrip("-*• ")
                if clean and clean not in results:
                    results.append(clean)

        for pat in constraint_patterns:
            for match in re.finditer(pat, source_text, re.MULTILINE):
                item = match.group(1).strip()
                if item and item not in results and len(item) < 150:
                    results.append(item)

        if not results and archetype:
            results.extend(archetype.get("constraints", []))

        return results

    def _extract_examples(
        self,
        statement: str,
        user_test_cases: list[dict[str, Any]] | None,
        archetype: dict[str, Any] | None,
    ) -> list[ProblemExample]:
        examples: list[ProblemExample] = []

        # 1. Check user test cases
        if user_test_cases:
            for tc in user_test_cases:
                in_val = str(tc.get("input", "")).strip()
                out_val = str(tc.get("expected_output", tc.get("output", ""))).strip()
                if in_val or out_val:
                    examples.append(ProblemExample(input_raw=in_val, output_raw=out_val, explanation="User provided"))

        # 2. Parse from problem statement
        pattern = re.compile(
            r"(?:Example\s*\d*[:\-]?\s*)?"
            r"Input:\s*(?P<input>[^\n]+)\s*\n"
            r"\s*Output:\s*(?P<output>[^\n]+)"
            r"(?:\s*\n\s*Explanation:\s*(?P<explanation>[^\n]+))?",
            re.IGNORECASE,
        )
        for m in pattern.finditer(statement):
            inp = m.group("input").strip()
            out = m.group("output").strip()
            exp = (m.group("explanation") or "").strip()
            if not any(e.input_raw == inp for e in examples):
                examples.append(ProblemExample(input_raw=inp, output_raw=out, explanation=exp))

        # 3. Fallback to archetype sample examples if none found
        if not examples and archetype and archetype.get("sample_examples"):
            examples.extend(archetype["sample_examples"])

        return examples

    def _extract_signature(self, code: str, statement: str, language: str) -> str | None:
        if not code:
            return None
        if language == "python":
            m = re.search(r"def\s+([a-zA-Z_]\w*\s*\([^)]*\))", code)
            if m:
                return m.group(0)
        elif language == "cpp":
            m = re.search(r"([a-zA-Z0-9_<>\s*&]+)\s+([a-zA-Z_]\w*\s*\([^)]*\))\s*\{", code)
            if m and "main" not in m.group(2):
                return m.group(0).rstrip("{").strip()
        elif language == "javascript":
            m = re.search(r"(?:function\s+([a-zA-Z_]\w*\s*\([^)]*\))|var\s+([a-zA-Z_]\w*)\s*=\s*function)", code)
            if m:
                return m.group(0)
        elif language == "java":
            m = re.search(r"(?:public|protected|private)?\s*(?:static)?\s*[\w<>[\]]+\s+([a-zA-Z_]\w*\s*\([^)]*\))\s*\{", code)
            if m and "main" not in m.group(1):
                return m.group(0).rstrip("{").strip()
        return None

    def _infer_edge_cases(self, constraints: list[str], archetype: dict[str, Any] | None) -> list[str]:
        edge_cases: list[str] = []
        if archetype and archetype.get("edge_cases"):
            edge_cases.extend(archetype["edge_cases"])

        # Infer from constraint text
        joined = " ".join(constraints).lower()
        if "0 <=" in joined or "length == 0" in joined or "0 <= n" in joined:
            edge_cases.append("Empty input collection (size 0)")
        if "1 <=" in joined or "length <= 1" in joined:
            edge_cases.append("Single-element collection (size 1)")
        if "-" in joined and ("<= nums" in joined or "<= prices" in joined or "negative" in joined):
            edge_cases.append("Negative numbers and boundary extremes")
        if "duplicate" in joined or "distinct" in joined or "unique" in joined:
            edge_cases.append("Repeated / identical duplicate elements")

        # De-duplicate while preserving order
        seen = set()
        deduped = []
        for ec in edge_cases:
            if ec not in seen:
                seen.add(ec)
                deduped.append(ec)
        return deduped

    def _infer_expected_complexity(self, constraints: list[str], archetype: dict[str, Any] | None) -> dict[str, str]:
        if archetype and archetype.get("expected_complexity"):
            return archetype["expected_complexity"]

        # Parse constraints for N upper bound
        max_n = 1000
        for c in constraints:
            m = re.search(r"10\^(\d+)", c)
            if m:
                exponent = int(m.group(1))
                max_n = max(max_n, 10**exponent)
            m2 = re.search(r"<=\s*(\d{4,})", c)
            if m2:
                max_n = max(max_n, int(m2.group(1)))

        if max_n >= 100_000:
            return {"time": "O(N) or O(N log N)", "space": "O(N) or O(1)"}
        elif max_n >= 10_000:
            return {"time": "O(N) or O(N log N)", "space": "O(N)"}
        elif max_n <= 50:
            return {"time": "O(N) or O(2^N)", "space": "O(N)"}
        return {"time": "O(N)", "space": "O(N)"}

    def _extract_input_description(self, statement: str, examples: list[ProblemExample]) -> str:
        if examples and examples[0].input_raw:
            return f"Input format illustrated by example: {examples[0].input_raw}"
        return "Input as described in the problem statement."

    def _extract_output_description(self, statement: str, examples: list[ProblemExample]) -> str:
        if examples and examples[0].output_raw:
            return f"Expected return format: {examples[0].output_raw}"
        return "Output matching specified return type."
