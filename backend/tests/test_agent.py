from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.agent_service import AgentService


@pytest.mark.asyncio
async def test_agent_chat_complexity_intent():
    transport = ASGITransport(app=app)
    with patch.object(AgentService, "_query_ollama", new_callable=AsyncMock) as mock_ollama:
        mock_ollama.return_value = None
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/agent/chat",
                json={
                    "code": "def find_max(arr):\n    m = arr[0]\n    for x in arr:\n        if x > m: m = x\n    return m",
                    "language": "python",
                    "user_message": "What is the Big-O time complexity of this code?",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert "O(N)" in data["reply"]
            assert "devlens-heuristic-copilot" in data["model"]


@pytest.mark.asyncio
async def test_agent_chat_edge_cases_intent():
    transport = ASGITransport(app=app)
    with patch.object(AgentService, "_query_ollama", new_callable=AsyncMock) as mock_ollama:
        mock_ollama.return_value = None
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/agent/chat",
                json={
                    "code": "def divide(a, b):\n    return a / b",
                    "language": "python",
                    "user_message": "Can you generate 3 edge cases and unit tests for this?",
                    "finding_summary": "ZeroDivisionError when b is 0",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert "Edge-Case" in data["reply"]
            assert data.get("code_snippet") is not None
            assert "run_tests" in data["code_snippet"]


@pytest.mark.asyncio
async def test_agent_chat_alternative_fix_intent():
    transport = ASGITransport(app=app)
    with patch.object(AgentService, "_query_ollama", new_callable=AsyncMock) as mock_ollama:
        mock_ollama.return_value = None
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/agent/chat",
                json={
                    "code": "def divide(a, b):\n    return a / b",
                    "language": "python",
                    "user_message": "Can you give me an alternative fix using guard clauses?",
                    "finding_summary": "Division by zero",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert "Alternative" in data["reply"]
            assert data.get("code_snippet") is not None


@pytest.mark.asyncio
async def test_agent_chat_greeting_intent():
    transport = ASGITransport(app=app)
    with patch.object(AgentService, "_query_ollama", new_callable=AsyncMock) as mock_ollama:
        mock_ollama.return_value = None
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/agent/chat",
                json={
                    "code": "int main() { return 0; }",
                    "language": "cpp",
                    "user_message": "hlooo",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert "Hello! I'm DevLens Copilot" in data["reply"]


@pytest.mark.asyncio
async def test_agent_chat_ollama_integration():
    transport = ASGITransport(app=app)
    mock_llm_reply = (
        "Here is an optimized solution:\n```python\ndef solve():\n    return True\n```"
    )
    with patch.object(AgentService, "_query_ollama", new_callable=AsyncMock) as mock_ollama:
        mock_ollama.return_value = mock_llm_reply
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/agent/chat",
                json={
                    "code": "def solve(): pass",
                    "language": "python",
                    "user_message": "How to implement this?",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "optimized solution" in data["reply"]
            assert data["code_snippet"] == "def solve():\n    return True"
            assert "ollama:" in data["model"]


@pytest.mark.asyncio
async def test_agent_chat_rejects_empty_user_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/agent/chat",
            json={
                "code": "print(1)",
                "language": "python",
                "user_message": "",
            },
        )
        assert resp.status_code == 422
