from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ProblemExample(BaseModel):
    input_raw: str
    output_raw: str
    explanation: str = ""
    parsed_input: Any = None
    parsed_output: Any = None


class ProblemContext(BaseModel):
    mode: str = "general"  # "general" | "leetcode"
    objective: str = ""
    input_description: str = ""
    output_description: str = ""
    constraints: list[str] = Field(default_factory=list)
    examples: list[ProblemExample] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    function_signature: str | None = None
    expected_complexity: dict[str, str] = Field(default_factory=lambda: {"time": "O(N)", "space": "O(N)"})
    language: str = "python"
    raw_statement: str = ""
    raw_constraints: str = ""
    problem_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
