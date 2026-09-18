from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class ExecutionOutput(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int
    execution_time_ms: int


class ExecutionUnavailable(RuntimeError):
    """Raised when the required sandbox cannot be used safely."""


class ExecutionService(ABC):
    @abstractmethod
    async def execute(self, language: str, code: str, stdin: str = "") -> ExecutionOutput:
        raise NotImplementedError

