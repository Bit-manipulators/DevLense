from __future__ import annotations

import pytest


def test_debug_endpoint_syntax_error(client):
    payload = {
        "mode": "general",
        "language": "python",
        "code": "def solve():\n    print('Unclosed string\n",
    }
    response = client.post("/api/v1/debug", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "python"
    assert data["status"] in ("fixed", "failed", "needs_review")
    assert data["failure_type"] in ("syntax", "compilation")
    assert "session_id" in data and data["session_id"] is not None


def test_debug_endpoint_two_sum_leetcode(client):
    payload = {
        "mode": "leetcode",
        "language": "python",
        "problem_statement": "Two Sum: Given an array of integers nums and an integer target, return indices of two numbers that add up to target.",
        "constraints": "2 <= nums.length <= 10^4",
        "code": "def twoSum(nums, target):\n    # Buggy: returns empty list\n    return []\n",
    }
    response = client.post("/api/v1/debug", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "python"
    assert data["status"] in ("fixed", "needs_review", "failed")
    assert len(data["iterations"]) >= 1
    assert data["validation"]["compile"] is True
    assert data["complexity"]["time_complexity"] is not None


def test_debug_endpoint_cpp_routing(client):
    payload = {
        "mode": "general",
        "language": "cpp",
        "code": "int main() { int arr[5] = {1,2,3,4,5}; for(int i = 0; i <= 5; i++) { } return 0; }",
    }
    response = client.post("/api/v1/debug", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "cpp"
    assert "python" not in data["problem_summary"].lower()


def test_debug_endpoint_unsupported_language(client):
    payload = {
        "mode": "general",
        "language": "haskell",
        "code": "main = putStrLn \"hello\"",
    }
    response = client.post("/api/v1/debug", json=payload)
    assert response.status_code in (400, 422, 500)
