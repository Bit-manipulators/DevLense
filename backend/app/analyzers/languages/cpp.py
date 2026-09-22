from __future__ import annotations

import re

from app.analyzers.base import AnalysisFinding
from app.analyzers.languages.base import LanguageAnalyzer


class CppAnalyzer(LanguageAnalyzer):
    """Deterministic C++ diagnostics."""

    def analyze(self, code: str, error_message: str = "", question: str = "") -> AnalysisFinding:
        # 1. Array with loop bound out-of-bounds
        array_loop = re.search(
            r"(?P<array>\w+)\s*\[\s*(?P<size>\d+)\s*\][\s\S]{0,500}?"
            r"for\s*\(\s*(?:int|size_t|long)\s+(?P<index>\w+)\s*=\s*0\s*;\s*"
            r"(?P=index)\s*<=\s*(?P<bound>\d+)\s*;[\s\S]{0,200}?"
            r"(?P=array)\s*\[\s*(?P=index)\s*\]",
            code,
        )
        if array_loop:
            size = int(array_loop.group("size"))
            bound = int(array_loop.group("bound"))
            if bound >= size:
                loop_line = code[: array_loop.start()].count("\n") + 1
                old = f"{array_loop.group('index')} <= {bound}"
                new = f"{array_loop.group('index')} < {size}"
                return self._finding(
                    summary="Possible array index out of bounds",
                    severity="high",
                    root_cause=(
                        f"The loop condition allows index {bound}, but {array_loop.group('array')} has valid indices 0 through {size - 1}."
                    ),
                    explanation=(
                        "C++ does not automatically check native array bounds. Reading past the array is undefined "
                        "behavior and can cause a segmentation fault."
                    ),
                    code=code,
                    suggested_fix=f"Replace `{old}` with `{new}`.",
                    corrected_code=code.replace(old, new, 1),
                    affected_lines=[loop_line],
                    confidence=0.96,
                    steps=[
                        "Use a strict `<` bound for an array of this size.",
                        "Prefer std::array or std::vector::at during debugging for bounds checks.",
                        "Compile with warnings enabled and rerun in the isolated sandbox.",
                    ],
                )

        # 2. General off-by-one loop condition (e.g. for(int i = 0; i <= n; i++))
        general_loop = re.search(
            r"for\s*\(\s*(?:int|size_t|auto|long)?\s*(?P<index>\w+)\s*=\s*0\s*;\s*"
            r"(?P=index)\s*<=\s*(?P<bound>[a-zA-Z0-9_.]+)\s*;",
            code,
        )
        if general_loop:
            index = general_loop.group("index")
            bound = general_loop.group("bound")
            loop_line = code[: general_loop.start()].count("\n") + 1
            old = f"{index} <= {bound}"
            new = f"{index} < {bound}"
            return self._finding(
                summary="Off-by-one loop boundary (possible buffer overflow or out of bounds)",
                severity="high",
                root_cause=f"The loop condition allows index equal to `{bound}`. In 0-indexed sequences of size `{bound}`, valid indices are 0 to `{bound} - 1`.",
                explanation=(
                    "In C++, arrays and containers are 0-indexed. Iterating with `<=` reaches element `bound`, "
                    "which is an off-by-one error when `bound` represents the total length or capacity."
                ),
                code=code,
                suggested_fix=f"Replace `{old}` with `{new}`.",
                corrected_code=code.replace(old, new, 1),
                affected_lines=[loop_line],
                confidence=0.95,
                steps=[
                    f"Replace `{old}` with `{new}`.",
                    "Ensure loop termination condition strictly tests bounds for 0-based indexing.",
                    "Rerun the program in the isolated sandbox.",
                ],
            )

        # 3. Null pointer dereference
        null_match = re.search(
            r"(?:\w+\s*\*\s*)(?P<name>\w+)\s*=\s*(?:nullptr|NULL|0)\s*;[\s\S]{0,400}?\b(?P=name)\s*->",
            code,
        )
        if null_match:
            line = code[: null_match.start()].count("\n") + 1
            name = null_match.group("name")
            return self._finding(
                summary="Null pointer dereference",
                severity="critical",
                root_cause=f"Pointer `{name}` is initialized to null and later dereferenced.",
                explanation="Dereferencing a null pointer invokes undefined behavior and commonly causes a segmentation fault.",
                code=code,
                suggested_fix=f"Initialize `{name}` to a valid object or guard it with `if ({name} != nullptr)` before dereferencing.",
                corrected_code=code.replace(f"{name}->", f"if ({name} != nullptr) {name}->", 1),
                affected_lines=[line],
                confidence=0.97,
            )

        # 4. Missing semicolon
        semicolon_line = self._line_of(code, r"(?:cout|return\s+\d+|int\s+\w+\s*=.+)\s*\n")
        if "expected ';'" in error_message.lower() and semicolon_line:
            lines = code.split("\n")
            if 0 < semicolon_line <= len(lines):
                target_idx = semicolon_line - 1
                if not lines[target_idx].rstrip().endswith(";"):
                    lines[target_idx] = lines[target_idx].rstrip() + ";"
            return self._finding(
                summary="Missing C++ semicolon",
                severity="high",
                root_cause="The compiler reports a statement that is not terminated with `;`.",
                explanation="Most C++ statements must end with a semicolon.",
                code=code,
                suggested_fix="Add a semicolon at the compiler-reported statement.",
                corrected_code="\n".join(lines),
                affected_lines=[semicolon_line],
                confidence=0.9,
            )

        # 5. Division by zero
        if re.search(r"/\s*0(?:\D|$)", code):
            line = self._line_of(code, r"/\s*0(?:\D|$)")
            corrected = re.sub(r"/\s*0(?:\D|$)", "/ denominator /* ensure non-zero */", code, count=1)
            return self._finding(
                summary="Division by zero",
                severity="high",
                root_cause="An expression divides by literal zero.",
                explanation="Integer division by zero is undefined behavior in C++.",
                code=code,
                suggested_fix="Validate the denominator before performing the division.",
                corrected_code=corrected,
                affected_lines=[line] if line else [],
                confidence=0.99,
            )

        return self._no_definite_match(code, "C++")
