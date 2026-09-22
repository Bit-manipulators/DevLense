from __future__ import annotations

import pytest
import shutil

from app.config import get_settings
from app.execution.process import ProcessExecutionService
from app.orchestrator.debug_orchestrator import DebugOrchestrator
from app.schemas.debug import DebugRequest


@pytest.mark.asyncio
async def test_live_python_debug_and_repair():
    settings = get_settings()
    proc_service = ProcessExecutionService(settings)
    orchestrator = DebugOrchestrator(proc_service, settings)

    # Buggy Python: loop bounds IndexError
    req = DebugRequest(
        mode="general",
        language="python",
        code="nums = [10, 20, 30]\nfor i in range(4):\n    print(nums[i])\n",
    )
    report = await orchestrator.debug(req)
    assert report.language == "python"
    assert report.status in ("fixed", "needs_review", "failed")
    assert any("index" in e.likely_root_cause.lower() or "bounds" in e.likely_root_cause.lower() for e in report.evidence)


@pytest.mark.asyncio
async def test_live_cpp_debug_never_routed_to_python():
    settings = get_settings()
    proc_service = ProcessExecutionService(settings)
    orchestrator = DebugOrchestrator(proc_service, settings)

    # C++ problem
    cpp_code = """#include <iostream>
using namespace std;
int main() {
    int arr[3] = {1, 2, 3};
    for (int i = 0; i < 3; i++) {
        cout << arr[i] << endl;
    }
    return 0;
}
"""
    req = DebugRequest(
        mode="general",
        language="cpp",
        code=cpp_code,
    )
    report = await orchestrator.debug(req)
    assert report.language == "cpp"
    assert "python" not in report.problem_summary.lower()
    # It passes cleanly
    assert report.status in ("passed", "fixed")


@pytest.mark.asyncio
async def test_live_javascript_debug():
    if not shutil.which("node"):
        pytest.skip("Node.js is not installed on host")

    settings = get_settings()
    proc_service = ProcessExecutionService(settings)
    orchestrator = DebugOrchestrator(proc_service, settings)

    # Buggy JavaScript: null reference
    js_code = """const user = null;
console.log(user.name);
"""
    req = DebugRequest(
        mode="general",
        language="javascript",
        code=js_code,
    )
    report = await orchestrator.debug(req)
    assert report.language == "javascript"
    assert report.status in ("fixed", "needs_review", "failed")
    assert any("null" in str(e).lower() or "typeerror" in str(e).lower() or "property" in str(e).lower() for e in report.evidence)


def test_api_javascript_array_prototype_last(client):
    code = "Array.prototype.last = function() {\n    return this[this.length - 1];\n};"
    res = client.post("/api/v1/analyze", json={"language": "javascript", "code": code})
    assert res.status_code == 201
    data = res.json()
    assert "No definite fault" not in data["summary"]
    assert "-1" in data["corrected_code"]
    assert data["severity"] in ("high", "medium")


def test_api_python_fibonacci_bottleneck(client):
    code = "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)\n"
    res = client.post("/api/v1/analyze", json={"language": "python", "code": code})
    assert res.status_code == 201
    data = res.json()
    assert "No definite fault" not in data["summary"]
    assert data["severity"] == "high"
    assert "Bottleneck" in data["summary"] or "TLE" in data["summary"] or "Complexity" in data["explanation"]


def test_api_clean_javascript_never_shows_rule_based_cant_find(client):
    code = "function add(a, b) {\n    return a + b;\n}\nconsole.log(add(2, 3));"
    res = client.post("/api/v1/analyze", json={"language": "javascript", "code": code})
    assert res.status_code == 201
    data = res.json()
    assert "No definite fault" not in data["summary"]
    assert "can't find" not in data["summary"].lower()
    assert data["severity"] == "low"

