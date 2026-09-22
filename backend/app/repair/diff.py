from __future__ import annotations

import difflib


class DiffGenerator:
    """Generates clean unified diffs and calculates affected line numbers."""

    @classmethod
    def generate_unified_diff(
        cls,
        original_code: str,
        corrected_code: str,
        filename: str = "solution",
    ) -> str:
        orig_lines = original_code.splitlines(keepends=True)
        corr_lines = corrected_code.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            corr_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
        return "".join(diff)

    @classmethod
    def compute_affected_lines(cls, original_code: str, corrected_code: str) -> list[int]:
        orig_lines = original_code.splitlines()
        corr_lines = corrected_code.splitlines()

        matcher = difflib.SequenceMatcher(None, orig_lines, corr_lines)
        affected = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                # 1-based indexing for lines
                for line_idx in range(i1 + 1, i2 + 1):
                    affected.append(line_idx)
                if not affected and i1 < len(orig_lines):
                    affected.append(i1 + 1)
        return sorted(list(set(affected)))
