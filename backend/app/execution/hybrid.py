from __future__ import annotations

from app.config import Settings
from app.execution.base import ExecutionOutput, ExecutionService
from app.execution.docker import DockerExecutionService
from app.execution.process import ProcessExecutionService


class HybridExecutionService(ExecutionService):
    """Executes code via Docker container if daemon is active, or via isolated subprocess on cloud hosts."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.docker_service = DockerExecutionService(settings)
        self.process_service = ProcessExecutionService(settings)

    def is_available(self) -> bool:
        return self.docker_service.is_available() or self.process_service.is_available()

    def get_mode(self) -> str:
        if self.docker_service.is_available():
            return "docker"
        if self.process_service.is_available():
            return "cloud_container"
        return "none"

    async def execute(self, language: str, code: str, stdin: str = "") -> ExecutionOutput:
        if self.docker_service.is_available():
            return await self.docker_service.execute(language, code, stdin)
        return await self.process_service.execute(language, code, stdin)
