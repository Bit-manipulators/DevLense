from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_agent_chat_complexity_intent():
    transport = ASGITransport(app=app)
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
        assert "model" in data


@pytest.mark.asyncio
async def test_agent_chat_edge_cases_intent():
    transport = ASGITransport(app=app)
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
