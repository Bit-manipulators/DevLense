from __future__ import annotations

import re
from typing import Any

from app.context.problem_context import ProblemContext
from app.languages.registry import LanguageRegistry
from app.testing.generator import TestCase
from app.testing.oracle import ExpectedResultEngine


class TestHarnessBuilder:
    """Wraps user functions with automated test runners for sandboxed execution."""

    @classmethod
    def prepare_executable_code(
        cls,
        code: str,
        language: str,
        test_case: TestCase | None,
        context: ProblemContext | None = None,
    ) -> tuple[str, str]:
        """Returns (executable_code, stdin_data)."""
        canonical_lang = LanguageRegistry.normalize(language)

        std_cpp_headers = (
            "#include <iostream>\n"
            "#include <vector>\n"
            "#include <string>\n"
            "#include <algorithm>\n"
            "#include <climits>\n"
            "#include <cmath>\n"
            "#include <unordered_map>\n"
            "#include <unordered_set>\n"
            "#include <queue>\n"
            "#include <stack>\n"
            "using namespace std;\n\n"
        )

        if not test_case or not test_case.input_raw:
            if canonical_lang == "cpp":
                prepared = code
                if "#include" not in code:
                    prepared = std_cpp_headers + prepared
                if "int main(" not in prepared:
                    prepared = prepared + "\nint main() { return 0; }\n"
                return prepared, ""
            return code, ""

        input_str = test_case.input_raw.strip()

        # 1. Python Function / Class Harness
        if canonical_lang == "python":
            cls_match = re.search(
                r"class\s+([a-zA-Z_]\w*):[\s\S]*?def\s+([a-zA-Z_]\w*)\s*\(self(?:,\s*([^)]*))?\)",
                code,
            )
            fn_match = re.search(r"def\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)", code)

            if cls_match and "_res =" not in code:
                cls_name = cls_match.group(1)
                fn_name = cls_match.group(2)
                try:
                    args = ExpectedResultEngine._parse_inputs(input_str)
                    args_repr = ", ".join(repr(a) for a in args)
                    harness = (
                        f"\n\nimport json\n"
                        f"_sol = {cls_name}()\n"
                        f"_res = _sol.{fn_name}({args_repr})\n"
                        f"if isinstance(_res, bool):\n"
                        f"    print('true' if _res else 'false')\n"
                        f"else:\n"
                        f"    print(json.dumps(_res, separators=(',', '')))\n"
                    )
                    return code + harness, ""
                except Exception:
                    pass
            elif fn_match and "_res =" not in code:
                fn_name = fn_match.group(1)
                try:
                    args = ExpectedResultEngine._parse_inputs(input_str)
                    args_repr = ", ".join(repr(a) for a in args)
                    harness = (
                        f"\n\nimport json\n"
                        f"_res = {fn_name}({args_repr})\n"
                        f"if isinstance(_res, bool):\n"
                        f"    print('true' if _res else 'false')\n"
                        f"else:\n"
                        f"    print(json.dumps(_res, separators=(',', '')))\n"
                    )
                    return code + harness, ""
                except Exception:
                    pass

        # 2. JavaScript Function / Prototype Harness
        if canonical_lang == "javascript":
            if "Array.prototype.last" in code and "console.log" not in code:
                try:
                    args = ExpectedResultEngine._parse_inputs(input_str)
                    raw_arg = args[0] if args else []
                    target_arr = raw_arg if isinstance(raw_arg, list) else ([raw_arg] if raw_arg != "" else [])
                    import json
                    harness = (
                        f"\n\nconst _arr = {json.dumps(target_arr)};\n"
                        f"console.log(JSON.stringify(_arr.last()));\n"
                    )
                    return code + harness, ""
                except Exception:
                    harness = "\n\nconsole.log(JSON.stringify([1,2,3].last()));\n"
                    return code + harness, ""


            fn_match = re.search(r"(?:function\s+([a-zA-Z_]\w*)|var\s+([a-zA-Z_]\w*)\s*=\s*function|const\s+([a-zA-Z_]\w*)\s*=\s*(?:function|\([^)]*\)\s*=>))", code)
            if fn_match and "console.log" not in code:
                fn_name = fn_match.group(1) or fn_match.group(2) or fn_match.group(3)
                try:
                    args = ExpectedResultEngine._parse_inputs(input_str)
                    import json
                    args_json = ", ".join(json.dumps(a) for a in args)
                    harness = (
                        f"\n\nconst _res = {fn_name}({args_json});\n"
                        f"console.log(JSON.stringify(_res));\n"
                    )
                    return code + harness, ""
                except Exception:
                    pass

        # 3. C++ Function / Class Harness
        if canonical_lang == "cpp":
            prepared = code
            if "#include" not in code:
                prepared = std_cpp_headers + prepared

            if "int main(" not in prepared:
                args = ExpectedResultEngine._parse_inputs(input_str)
                is_class_solution = "class Solution" in prepared

                # Fibonacci C++ harness
                if "fib" in prepared:
                    n_val = int(args[0]) if args else 2
                    caller = "sol.fib" if is_class_solution else "fib"
                    decl = "Solution sol;\n" if is_class_solution else ""
                    harness = (
                        f"\nint main() {{\n"
                        f"    {decl}"
                        f"    std::cout << {caller}({n_val}) << std::endl;\n"
                        f"    return 0;\n"
                        f"}}\n"
                    )
                    return prepared + harness, ""

                # Two Sum C++ harness
                if "twoSum" in prepared:
                    if len(args) == 2 and isinstance(args[0], list):
                        nums_str = ", ".join(str(x) for x in args[0])
                        target_val = args[1]
                        caller = "sol.twoSum" if is_class_solution else "twoSum"
                        decl = "Solution sol;\n" if is_class_solution else ""
                        harness = (
                            f"\nint main() {{\n"
                            f"    {decl}"
                            f"    std::vector<int> nums = {{{nums_str}}};\n"
                            f"    std::vector<int> res = {caller}(nums, {target_val});\n"
                            f"    std::cout << \"[\";\n"
                            f"    for (size_t i = 0; i < res.size(); i++) {{\n"
                            f"        std::cout << res[i] << (i + 1 < res.size() ? \",\" : \"\");\n"
                            f"    }}\n"
                            f"    std::cout << \"]\" << std::endl;\n"
                            f"    return 0;\n"
                            f"}}\n"
                        )
                        return prepared + harness, ""

                # Fallback C++ runner
                prepared = prepared + "\nint main() { return 0; }\n"
                return prepared, input_str

        # Default fallback: pass test input via stdin
        return code, input_str
