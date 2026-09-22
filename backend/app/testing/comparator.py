from __future__ import annotations

import json
import re


class OutputComparator:
    """Safe semantic and format-tolerant output comparator."""

    @classmethod
    def compare(cls, expected: str | None, actual: str | None) -> tuple[bool, str]:
        if expected is None:
            return True, "No expected oracle specified; execution succeeded."

        exp_clean = str(expected).strip()
        act_clean = str(actual).strip() if actual is not None else ""

        # Exact match
        if exp_clean == act_clean:
            return True, "Exact match."

        # 1. JSON parsing comparison (arrays, dicts, booleans, numbers)
        try:
            exp_json = cls._parse_loose_json(exp_clean)
            act_json = cls._parse_loose_json(act_clean)
            if exp_json is not None and act_json is not None:
                if exp_json == act_json:
                    return True, "JSON / semantic value match."
                # Allow sorted index pairs if problem is Two Sum
                if isinstance(exp_json, list) and isinstance(act_json, list):
                    if sorted(exp_json) == sorted(act_json):
                        return True, "Collection permutation match."
        except Exception:
            pass

        # 2. Boolean normalization
        if exp_clean.lower() in ("true", "false") and act_clean.lower() in ("true", "false"):
            if exp_clean.lower() == act_clean.lower():
                return True, "Boolean match."
            return False, f"Expected boolean '{exp_clean}', but got '{act_clean}'."

        # 3. Numeric float tolerance
        try:
            exp_num = float(exp_clean)
            act_num = float(act_clean)
            if abs(exp_num - act_num) < 1e-5:
                return True, "Numeric float match within tolerance."
        except ValueError:
            pass

        # 4. Whitespace and bracket normalization
        norm_exp = re.sub(r"\s+", " ", exp_clean)
        norm_act = re.sub(r"\s+", " ", act_clean)
        norm_exp = norm_exp.replace(" ,", ",").replace(", ", ",")
        norm_act = norm_act.replace(" ,", ",").replace(", ", ",")
        if norm_exp == norm_act:
            return True, "Normalized whitespace match."

        return False, f"Expected '{exp_clean}', but got '{act_clean}'."

    @classmethod
    def _parse_loose_json(cls, text: str):
        # Convert single quotes or Python booleans to valid JSON
        t = text.replace("True", "true").replace("False", "false").replace("None", "null")
        t = re.sub(r"'([^']*)'", r'"\1"', t)
        try:
            return json.loads(t)
        except Exception:
            return None
