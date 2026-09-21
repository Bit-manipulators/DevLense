from __future__ import annotations

import asyncio
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from app.config import Settings
from app.execution.base import ExecutionOutput, ExecutionService, ExecutionUnavailable


class ProcessExecutionService(ExecutionService):
    """Isolated subprocess execution service with timeouts and output bounds.

    Used inside cloud container environments (such as Render) where nested Docker
    daemons are not available, or for local development without Docker Desktop.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def is_available(self) -> bool:
        return bool(sys.executable or shutil.which("python3") or shutil.which("python"))

    def _get_command(self, language: str, workspace: Path, filename: str) -> list[str] | None:
        file_path = str(workspace / filename)
        if language == "python":
            py_bin = sys.executable or shutil.which("python3") or "python"
            return [py_bin, "-I", "-s", file_path]
        if language == "javascript":
            node_bin = shutil.which("node") or shutil.which("nodejs")
            if node_bin:
                return [node_bin, file_path]
        if language == "cpp":
            gpp_bin = shutil.which("g++")
            if gpp_bin:
                out_path = str(workspace / ("program.exe" if sys.platform == "win32" else "program"))
                return [gpp_bin, "-std=c++17", "-O2", file_path, "-o", out_path]
        if language == "java":
            java_bin = shutil.which("java")
            if java_bin:
                return [java_bin, file_path]
        return None

    def _trim(self, value: bytes) -> str:
        text = value.decode("utf-8", errors="replace")
        limit = self.settings.max_output_size
        if len(text) > limit:
            return text[:limit] + "\n[output truncated by DevLens]"
        return text

    async def execute(self, language: str, code: str, stdin: str = "") -> ExecutionOutput:
        filenames = {
            "python": "main.py",
            "javascript": "main.js",
            "cpp": "main.cpp",
            "java": "Main.java",
        }
        if language not in filenames:
            raise ExecutionUnavailable(f"Execution is not supported for {language}.")

        filename = filenames[language]
        with tempfile.TemporaryDirectory(prefix="devlens-proc-") as temp_dir:
            workspace = Path(temp_dir)
            source_file = workspace / filename
            source_file.write_text(code, encoding="utf-8")

            started = time.perf_counter()

            if language == "cpp":
                gpp_bin = shutil.which("g++")
                if not gpp_bin:
                    raise ExecutionUnavailable("C++ compiler (g++) is not installed on this server host.")
                out_bin = workspace / ("program.exe" if sys.platform == "win32" else "program")
                compile_proc = await asyncio.create_subprocess_exec(
                    gpp_bin, "-std=c++17", "-O2", str(source_file), "-o", str(out_bin),
                    cwd=str(workspace),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    c_out, c_err = await asyncio.wait_for(
                        compile_proc.communicate(),
                        timeout=self.settings.execution_timeout_seconds,
                    )
                except TimeoutError:
                    compile_proc.kill()
                    return ExecutionOutput(
                        success=False,
                        stdout="",
                        stderr="Compilation timed out.",
                        exit_code=124,
                        execution_time_ms=int((time.perf_counter() - started) * 1_000),
                    )
                if compile_proc.returncode != 0:
                    return ExecutionOutput(
                        success=False,
                        stdout=self._trim(c_out),
                        stderr=self._trim(c_err),
                        exit_code=compile_proc.returncode or 1,
                        execution_time_ms=int((time.perf_counter() - started) * 1_000),
                    )
                cmd = [str(out_bin)]
            else:
                cmd = self._get_command(language, workspace, filename)
                if not cmd:
                    raise ExecutionUnavailable(f"Runtime interpreter for {language} is not installed on this server.")

            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=str(workspace),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(stdin.encode("utf-8")),
                        timeout=self.settings.execution_timeout_seconds,
                    )
                except TimeoutError:
                    process.kill()
                    await process.communicate()
                    elapsed = int((time.perf_counter() - started) * 1_000)
                    return ExecutionOutput(
                        success=False,
                        stdout="",
                        stderr=f"Execution timed out after {self.settings.execution_timeout_seconds} seconds. Process terminated.",
                        exit_code=124,
                        execution_time_ms=elapsed,
                    )
            except OSError as exc:
                raise ExecutionUnavailable(f"Failed to start execution process: {exc}") from exc

            elapsed = int((time.perf_counter() - started) * 1_000)
            return ExecutionOutput(
                success=process.returncode == 0,
                stdout=self._trim(stdout),
                stderr=self._trim(stderr),
                exit_code=process.returncode or 0,
                execution_time_ms=elapsed,
            )
