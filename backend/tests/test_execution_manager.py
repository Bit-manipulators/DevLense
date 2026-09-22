from __future__ import annotations

import pytest

from app.execution.base import ExecutionOutput, ExecutionService
from app.execution.manager import ExecutionManager


class MockSandbox(ExecutionService):
    def __init__(self, output: ExecutionOutput):
        self._output = output

    async def execute(self, language: str, code: str, stdin: str = "") -> ExecutionOutput:
        return self._output


@pytest.mark.asyncio
async def test_execution_manager_success():
    mock = MockSandbox(ExecutionOutput(success=True, stdout="Hello World\n", stderr="", exit_code=0, execution_time_ms=15))
    mgr = ExecutionManager(mock)
    res = await mgr.execute("python", "print('Hello World')")
    assert res.success is True
    assert res.status == "success"
    assert res.phase == "runtime"
    assert res.stdout == "Hello World\n"


@pytest.mark.asyncio
async def test_execution_manager_cpp_compile_error():
    err_out = ExecutionOutput(
        success=False,
        stdout="",
        stderr="main.cpp:5:10: error: expected ';' before 'return'",
        exit_code=1,
        execution_time_ms=45,
    )
    mock = MockSandbox(err_out)
    mgr = ExecutionManager(mock)
    res = await mgr.execute("cpp", "int main() { return 0 }")
    assert res.success is False
    assert res.status == "compile_error"
    assert res.phase == "compile"
    assert "error: expected ';'" in res.stderr


@pytest.mark.asyncio
async def test_execution_manager_runtime_timeout():
    timeout_out = ExecutionOutput(
        success=False,
        stdout="",
        stderr="Execution timed out after 5 seconds. Process terminated.",
        exit_code=124,
        execution_time_ms=5002,
    )
    mock = MockSandbox(timeout_out)
    mgr = ExecutionManager(mock)
    res = await mgr.execute("python", "while True: pass")
    assert res.success is False
    assert res.status == "timeout"
    assert res.phase == "runtime"


@pytest.mark.asyncio
async def test_execution_manager_runtime_exception():
    runtime_err = ExecutionOutput(
        success=False,
        stdout="",
        stderr="Traceback (most recent call last):\n  File 'main.py', line 2, in <module>\nIndexError: list index out of range",
        exit_code=1,
        execution_time_ms=25,
    )
    mock = MockSandbox(runtime_err)
    mgr = ExecutionManager(mock)
    res = await mgr.execute("python", "arr = []\nprint(arr[0])")
    assert res.success is False
    assert res.status == "runtime_error"
    assert res.phase == "runtime"
