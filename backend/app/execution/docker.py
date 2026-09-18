from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from app.config import Settings
from app.execution.base import ExecutionOutput, ExecutionService, ExecutionUnavailable


class DockerExecutionService(ExecutionService):
    """Runs code only in a constrained Docker container.

    No local execution fallback is provided. Executing untrusted code on the API
    host is explicitly unsafe, so a missing Docker daemon is a configuration error.
    """

    _LANGUAGES = {
        "python": ("python:3.12-alpine", "main.py", ["python", "/workspace/main.py"]),
        "javascript": ("node:20-alpine", "main.js", ["node", "/workspace/main.js"]),
        "cpp": (
            "gcc:14.2.0",
            "main.cpp",
            ["sh", "-c", "g++ -std=c++17 -O2 -Wall /workspace/main.cpp -o /workspace/program && /workspace/program"],
        ),
        "java": (
            "eclipse-temurin:21-alpine",
            "Main.java",
            ["java", "/workspace/Main.java"],
        ),
    }

    def __init__(self, settings: Settings):
        self.settings = settings

    @staticmethod
    def is_available() -> bool:
        if shutil.which("docker") is None:
            return False
        try:
            proc = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
            return proc.returncode == 0
        except Exception:
            return False

    def _command(
        self, image: str, command: list[str], workspace: Path, container_name: str | None = None
    ) -> list[str]:
        # Every Docker argument is fixed by the server; user code is written as a
        # file and never interpolated into a host shell command.
        args = [
            "docker",
            "run",
            "--rm",
            "--interactive",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "64",
            "--memory",
            f"{self.settings.execution_memory_limit_mb}m",
            "--cpus",
            "0.5",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "-v",
            f"{workspace.resolve()}:/workspace:rw",
            "--workdir",
            "/workspace",
        ]
        if container_name:
            args.extend(["--name", container_name])
        args.append(image)
        args.extend(command)
        return args

    def _trim(self, value: bytes) -> str:
        text = value.decode("utf-8", errors="replace")
        limit = self.settings.max_output_size
        if len(text) > limit:
            return text[:limit] + "\n[output truncated by DevLens]"
        return text

    async def execute(self, language: str, code: str, stdin: str = "") -> ExecutionOutput:
        if language not in self._LANGUAGES:
            raise ExecutionUnavailable(f"Execution is not supported for {language}.")
        if not self.is_available():
            raise ExecutionUnavailable(
                "Docker is required for secure code execution but is not available. "
                "Install and start Docker Desktop, then retry."
            )

        image, filename, run_command = self._LANGUAGES[language]
        container_name = f"devlens-exec-{uuid.uuid4().hex[:12]}"
        with tempfile.TemporaryDirectory(prefix="devlens-exec-") as temp_dir:
            workspace = Path(temp_dir)
            (workspace / filename).write_text(code, encoding="utf-8")
            started = time.perf_counter()
            try:
                process = await asyncio.create_subprocess_exec(
                    *self._command(image, run_command, workspace, container_name=container_name),
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
                    # Explicitly remove the container in Docker daemon to prevent orphans
                    try:
                        cleanup = await asyncio.create_subprocess_exec(
                            "docker", "rm", "-f", container_name,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL,
                        )
                        await asyncio.wait_for(cleanup.wait(), timeout=3.0)
                    except Exception:
                        pass
                    elapsed = int((time.perf_counter() - started) * 1_000)
                    return ExecutionOutput(
                        success=False,
                        stdout="",
                        stderr=(
                            f"Execution timed out after {self.settings.execution_timeout_seconds} seconds. "
                            "The sandbox process was terminated."
                        ),
                        exit_code=124,
                        execution_time_ms=elapsed,
                    )
            except OSError as exc:
                raise ExecutionUnavailable("Docker could not start the secure execution sandbox.") from exc

            elapsed = int((time.perf_counter() - started) * 1_000)
            stderr_trimmed = self._trim(stderr)

            # Check if docker CLI returned failure because the daemon is not running
            if process.returncode != 0 and any(
                phrase in stderr_trimmed.lower()
                for phrase in [
                    "cannot connect to the docker daemon",
                    "is the docker daemon running",
                    "error during connect",
                    "docker daemon is not running",
                ]
            ):
                raise ExecutionUnavailable(
                    "Docker daemon is not running or cannot be reached. Start Docker Desktop, then retry."
                )

            return ExecutionOutput(
                success=process.returncode == 0,
                stdout=self._trim(stdout),
                stderr=stderr_trimmed,
                exit_code=process.returncode or 0,
                execution_time_ms=elapsed,
            )

