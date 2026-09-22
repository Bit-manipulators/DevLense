from __future__ import annotations

import re
from typing import Literal
from pydantic import BaseModel

from app.execution.base import ExecutionOutput, ExecutionService, ExecutionUnavailable
from app.languages.registry import LanguageRegistry

ExecutionStatus = Literal["success", "compile_error", "runtime_error", "timeout", "resource_error"]


class DetailedExecutionResult(BaseModel):
    success: bool
    status: ExecutionStatus
    phase: Literal["compile", "runtime"]
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: int = 0


class ExecutionManager:
    """Orchestrates compilation and sandboxed execution with structured evidence classification."""

    def __init__(self, execution_service: ExecutionService):
        self.service = execution_service

    async def execute(
        self,
        language: str,
        source_code: str,
        stdin: str = "",
    ) -> DetailedExecutionResult:
        canonical_lang = LanguageRegistry.normalize(language)

        try:
            output: ExecutionOutput = await self.service.execute(
                canonical_lang, source_code, stdin
            )
        except ExecutionUnavailable as exc:
            return DetailedExecutionResult(
                success=False,
                status="resource_error",
                phase="runtime",
                stdout="",
                stderr=f"Execution environment unavailable: {exc}",
                exit_code=-1,
                execution_time_ms=0,
            )

        return self._classify_output(canonical_lang, output)

    def _classify_output(self, language: str, output: ExecutionOutput) -> DetailedExecutionResult:
        stdout = output.stdout
        stderr = output.stderr
        exit_code = output.exit_code
        elapsed = output.execution_time_ms

        if output.success and exit_code == 0:
            return DetailedExecutionResult(
                success=True,
                status="success",
                phase="runtime",
                stdout=stdout,
                stderr=stderr,
                exit_code=0,
                execution_time_ms=elapsed,
            )

        # 1. Timeout Check
        if exit_code == 124 or "timed out" in stderr.lower():
            return DetailedExecutionResult(
                success=False,
                status="timeout",
                phase="runtime",
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time_ms=elapsed,
            )

        # 2. Compilation Error Classification
        is_compiled = LanguageRegistry.get(language).is_compiled
        compile_patterns = [
            r"error:",
            r"fatal error:",
            r"compilation terminated",
            r"syntax error",
            r"undefined reference to",
            r"cannot find symbol",
            r"Compilation timed out",
            r"Main\.java:\d+: error:",
            r"main\.cpp:\d+:\d+: error:",
        ]

        if is_compiled:
            if any(re.search(pat, stderr, re.IGNORECASE) for pat in compile_patterns):
                return DetailedExecutionResult(
                    success=False,
                    status="compile_error",
                    phase="compile",
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code or 1,
                    execution_time_ms=elapsed,
                )

        if language == "python" and ("SyntaxError:" in stderr or "IndentationError:" in stderr):
            return DetailedExecutionResult(
                success=False,
                status="compile_error",
                phase="compile",
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code or 1,
                execution_time_ms=elapsed,
            )

        # 3. Out of Memory / Resource Error
        if "out of memory" in stderr.lower() or "killed" in stderr.lower() or exit_code == 137:
            return DetailedExecutionResult(
                success=False,
                status="resource_error",
                phase="runtime",
                stdout=stdout,
                stderr=stderr or "Process terminated due to memory limit exhaustion.",
                exit_code=exit_code or 137,
                execution_time_ms=elapsed,
            )

        # 4. Default: Runtime Failure
        return DetailedExecutionResult(
            success=False,
            status="runtime_error",
            phase="runtime",
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code or 1,
            execution_time_ms=elapsed,
        )
