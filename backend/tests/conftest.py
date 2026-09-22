from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.execution.base import ExecutionOutput, ExecutionService
from app.main import app


class FakeSandbox(ExecutionService):
    """Predictable secure-sandbox stand-in for API integration tests."""

    @staticmethod
    def is_available() -> bool:
        return True

    async def execute(self, language: str, code: str, stdin: str = "") -> ExecutionOutput:
        if "INFINITE_LOOP" in code:
            return ExecutionOutput(
                success=False, stdout="", stderr="Execution timed out after 5 seconds.", exit_code=124, execution_time_ms=5_001
            )
        if "COMPILE_ERROR" in code:
            return ExecutionOutput(
                success=False, stdout="", stderr="main.cpp:1: error: expected ';'", exit_code=1, execution_time_ms=35
            )
        return ExecutionOutput(
            success=True, stdout=f"ran {language}: {stdin}".strip(), stderr="", exit_code=0, execution_time_ms=18
        )


@pytest.fixture()
def client(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'devlens-test.db').as_posix()}"
    database.configure_database(database_url)
    try:
        with TestClient(app) as test_client:
            app.state.execution_service = FakeSandbox()
            from app.analyzers.rule_based import RuleBasedAnalyzer
            from app.orchestrator.debug_orchestrator import DebugOrchestrator
            from app.services.analysis_service import AnalysisService

            app.state.debug_orchestrator = DebugOrchestrator(execution_service=app.state.execution_service)
            app.state.analysis_service = AnalysisService(
                analyzer=RuleBasedAnalyzer(),
                debug_orchestrator=app.state.debug_orchestrator,
            )
            yield test_client
    finally:
        database.Base.metadata.drop_all(bind=database.engine)
        database.engine.dispose()
