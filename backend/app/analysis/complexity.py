from __future__ import annotations

import ast
import re
from pydantic import BaseModel


class ComplexityReport(BaseModel):
    time_complexity: str = "O(N)"
    space_complexity: str = "O(1)"
    is_estimated: bool = True
    details: str = ""
    is_bottleneck: bool = False
    warning: str | None = None


class ComplexityAnalyzer:
    """Estimates time and space complexity and validates against constraints."""

    @classmethod
    def analyze(
        cls,
        code: str,
        language: str,
        constraints: list[str] | None = None,
    ) -> ComplexityReport:
        clean_code = cls._strip_comments(code, language)
        time_comp, space_comp, details = cls._estimate_complexity(clean_code, language)

        warning: str | None = None
        is_bottleneck = False

        # Constraint check: Compare against problem bounds
        if constraints:
            max_n = cls._extract_max_n(constraints)
            if max_n >= 10_000 and time_comp in ("O(N²)", "O(N^2)", "O(2^N)"):
                is_bottleneck = True
                warning = (
                    f"Estimated time complexity {time_comp} is likely too slow for stated constraint "
                    f"N ≈ {max_n:,}. A quadratic solution requires ≈ {max_n**2:,} operations and will likely "
                    "result in a Time Limit Exceeded (TLE). Consider optimizing to O(N) or O(N log N)."
                )

        if time_comp == "O(2^N)":
            is_bottleneck = True
            warning = (
                "Estimated time complexity O(2^N) is exponential due to unmemoized recursive branching. "
                "For N >= 30, this requires over 10^9 operations and will result in a Time Limit Exceeded (TLE). "
                "Consider optimizing using dynamic programming, memoization, or an iterative O(N) loop."
            )

        return ComplexityReport(
            time_complexity=time_comp,
            space_complexity=space_comp,
            is_estimated=True,
            details=details,
            is_bottleneck=is_bottleneck,
            warning=warning,
        )

    @classmethod
    def _strip_comments(cls, code: str, language: str) -> str:
        lines = []
        for line in code.splitlines():
            if language == "python":
                stripped = line.split("#")[0]
            else:
                stripped = line.split("//")[0]
            lines.append(stripped)
        return "\n".join(lines)

    @classmethod
    def _estimate_complexity(cls, code: str, language: str) -> tuple[str, str, str]:
        # Python AST analysis if Python
        if language == "python":
            return cls._estimate_python_ast(code)

        # Multi-language lexical/syntax loop analysis (C++, JS, Java)
        return cls._estimate_c_style(code, language)

    @classmethod
    def _estimate_python_ast(cls, code: str) -> tuple[str, str, str]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fall back to token scan if code has syntax errors
            return cls._estimate_c_style(code, "python")

        max_loop_depth = 0
        has_sort = False
        has_hashmap = False
        has_recursion = False

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_loop_depth = 0
                self.max_depth = 0
                self.func_defs = set()
                self.has_recursion = False
                self.has_sort = False
                self.has_hashmap = False

            def visit_FunctionDef(self, node):
                self.func_defs.add(node.name)
                self.generic_visit(node)

            def visit_For(self, node):
                self.current_loop_depth += 1
                self.max_depth = max(self.max_depth, self.current_loop_depth)
                self.generic_visit(node)
                self.current_loop_depth -= 1

            def visit_While(self, node):
                self.current_loop_depth += 1
                self.max_depth = max(self.max_depth, self.current_loop_depth)
                self.generic_visit(node)
                self.current_loop_depth -= 1

            def visit_Call(self, node):
                # Detect sort / sorted
                if isinstance(node.func, ast.Name) and node.func.id == "sorted":
                    self.has_sort = True
                elif isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
                    self.has_sort = True
                elif isinstance(node.func, ast.Name) and node.func.id in self.func_defs:
                    self.has_recursion = True
                self.generic_visit(node)

            def visit_Dict(self, node):
                self.has_hashmap = True
                self.generic_visit(node)

            def visit_Set(self, node):
                self.has_hashmap = True
                self.generic_visit(node)

        visitor = ComplexityVisitor()
        visitor.visit(tree)

        max_loop_depth = visitor.max_depth
        has_sort = visitor.has_sort
        has_hashmap = visitor.has_hashmap or "dict(" in code or "set(" in code or "{}" in code
        has_recursion = visitor.has_recursion

        # Detect binary search patterns
        is_binary_search = "// 2" in code or ">> 1" in code or "mid =" in code
        has_multi_recursion = bool(
            re.search(r"(\w+)\s*\([^)]*-\s*1\s*\)[\s\S]{1,50}?\1\s*\([^)]*-\s*2\s*\)", code)
            or re.search(r"(\w+)\s*\([^)]*-\s*2\s*\)[\s\S]{1,50}?\1\s*\([^)]*-\s*1\s*\)", code)
        )

        if has_multi_recursion:
            time_comp = "O(2^N)"
            details = "Recursive branching (T(n) = T(n-1) + T(n-2)) without memoization."
        elif is_binary_search and max_loop_depth == 1:
            time_comp = "O(log N)"
            details = "Binary search halving search space on each iteration."
        elif has_recursion and max_loop_depth >= 1:
            time_comp = "O(N²)"
            details = "Recursive branching with iterative loop traversal."
        elif max_loop_depth >= 2:
            time_comp = "O(N²)"
            details = f"Nested loop structure with nesting depth {max_loop_depth}."
        elif has_sort:
            time_comp = "O(N log N)"
            details = "Sorting invocation dominates execution time."
        elif max_loop_depth == 1:
            time_comp = "O(N)"
            details = "Single loop processing elements in linear pass."
        else:
            time_comp = "O(1)"
            details = "Constant time operations without iterative loops."

        space_comp = "O(N)" if (has_hashmap or "[" in code or "list(" in code) else "O(1)"
        return time_comp, space_comp, details

    @classmethod
    def _estimate_c_style(cls, code: str, language: str) -> tuple[str, str, str]:
        # Count loop statements and estimate nesting depth
        for_count = len(re.findall(r"\bfor\s*\(", code)) + (1 if language == "python" and "for " in code else 0)
        while_count = len(re.findall(r"\bwhile\s*\(", code)) + (1 if language == "python" and "while " in code else 0)

        # Estimate nesting depth by brace levels
        max_loop_depth = 0
        current_depth = 0
        in_loop_stack: list[int] = []

        lines = code.splitlines()
        for line in lines:
            trimmed = line.strip()
            if re.search(r"\b(for|while)\b", trimmed):
                current_depth += 1
                in_loop_stack.append(current_depth)
                max_loop_depth = max(max_loop_depth, len(in_loop_stack))
            if "}" in trimmed and in_loop_stack:
                in_loop_stack.pop()

        # If indentation based (python fallback)
        if max_loop_depth == 0 and (for_count + while_count) >= 2:
            # Check indentation difference
            loop_indents = []
            for line in lines:
                if re.search(r"^\s*(for|while)\b", line):
                    loop_indents.append(len(line) - len(line.lstrip()))
            if len(loop_indents) >= 2 and loop_indents[1] > loop_indents[0]:
                max_loop_depth = 2

        has_sort = bool(re.search(r"\b(std::sort|sort\(|\.sort\()", code))
        is_binary_search = bool(re.search(r"(mid\s*=\s*\(|mid\s*=\s*low|mid\s*=\s*left|>>\s*1|/\s*2)", code))
        has_hashmap = bool(
            re.search(r"\b(unordered_map|unordered_set|HashMap|HashSet|Map|Set|dict)\b", code)
        )

        has_multi_recursion = bool(
            re.search(r"(\w+)\s*\([^)]*-\s*1\s*\)[\s\S]{1,50}?\1\s*\([^)]*-\s*2\s*\)", code)
            or re.search(r"(\w+)\s*\([^)]*-\s*2\s*\)[\s\S]{1,50}?\1\s*\([^)]*-\s*1\s*\)", code)
        )

        if has_multi_recursion:
            time_comp = "O(2^N)"
            details = "Recursive branching (T(n) = T(n-1) + T(n-2)) without memoization."
        elif is_binary_search and (for_count + while_count) <= 1:
            time_comp = "O(log N)"
            details = "Binary search halving search space per iteration."
        elif max_loop_depth >= 2 or (for_count >= 2 and max_loop_depth >= 2):
            time_comp = "O(N²)"
            details = f"Nested loop structure detected with maximum nesting depth {max_loop_depth}."
        elif has_sort:
            time_comp = "O(N log N)"
            details = "Governed by comparison sorting."
        elif (for_count + while_count) >= 1:
            time_comp = "O(N)"
            details = "Single loop processing elements in linear pass."
        else:
            time_comp = "O(1)"
            details = "Constant time operations."


        space_comp = "O(N)" if (has_hashmap or "vector<" in code or "new " in code or "malloc" in code or "[" in code) else "O(1)"
        return time_comp, space_comp, details

    @classmethod
    def _extract_max_n(cls, constraints: list[str]) -> int:
        max_n = 1_000
        for c in constraints:
            m1 = re.search(r"10\^(\d+)", c)
            if m1:
                exponent = int(m1.group(1))
                max_n = max(max_n, 10**exponent)
            m2 = re.search(r"<=\s*(\d{4,})", c)
            if m2:
                max_n = max(max_n, int(m2.group(1)))
        return max_n
