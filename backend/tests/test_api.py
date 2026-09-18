from __future__ import annotations


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["execution_sandbox_available"] is True


def test_cors_accepts_expo_web_origin(client):
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_analyze_python_and_persist_session(client):
    payload = {
        "language": "python",
        "code": "numbers = [1, 2, 3]\nfor i in range(4):\n    print(numbers[i])\n",
        "error_message": "IndexError: list index out of range",
        "question": "Why does this crash?",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 201
    result = response.json()
    assert result["severity"] == "high"
    assert result["confidence"] >= 0.9
    assert "range(len(numbers))" in result["corrected_code"]

    history = client.get("/api/v1/sessions")
    assert history.status_code == 200
    assert history.json()[0]["id"] == result["session_id"]

    detail = client.get(f"/api/v1/sessions/{result['session_id']}")
    assert detail.status_code == 200
    assert detail.json()["code"] == payload["code"]


def test_analyze_cpp_array_bound(client):
    response = client.post(
        "/api/v1/analyze",
        json={
            "language": "cpp",
            "code": "int main() {\n int arr[5] = {1,2,3,4,5};\n for(int i = 0; i <= 5; i++) {\n  int x = arr[i];\n }\n}\n",
            "error_message": "segmentation fault",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["summary"] == "Possible array index out of bounds"
    assert "i < 5" in body["corrected_code"]


def test_rejects_invalid_or_unsupported_requests(client):
    blank = client.post("/api/v1/analyze", json={"language": "python", "code": "   "})
    unsupported = client.post("/api/v1/analyze", json={"language": "rust", "code": "fn main() {}"})
    assert blank.status_code == 422
    assert unsupported.status_code == 422


def test_execution_success_failure_timeout_and_session_delete(client):
    analysis = client.post(
        "/api/v1/analyze", json={"language": "python", "code": "print('hello')"}
    ).json()
    success = client.post(
        "/api/v1/execute",
        json={"language": "python", "code": "print('hello')", "stdin": "world", "session_id": analysis["session_id"]},
    )
    compile_failure = client.post(
        "/api/v1/execute",
        json={"language": "cpp", "code": "COMPILE_ERROR"},
    )
    timeout = client.post(
        "/api/v1/execute",
        json={"language": "python", "code": "INFINITE_LOOP"},
    )
    assert success.json()["success"] is True
    assert compile_failure.json()["success"] is False
    assert "error" in compile_failure.json()["stderr"]
    assert timeout.json()["exit_code"] == 124

    deleted = client.delete(f"/api/v1/sessions/{analysis['session_id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/sessions/{analysis['session_id']}").status_code == 404


def test_sessions_pagination(client):
    for i in range(5):
        client.post("/api/v1/analyze", json={"language": "python", "code": f"x = {i}"})

    first_page = client.get("/api/v1/sessions?limit=2&offset=0")
    assert first_page.status_code == 200
    assert len(first_page.json()) == 2

    second_page = client.get("/api/v1/sessions?limit=2&offset=2")
    assert second_page.status_code == 200
    assert len(second_page.json()) == 2

    # Verify no overlapping items between pages
    ids_first = {item["id"] for item in first_page.json()}
    ids_second = {item["id"] for item in second_page.json()}
    assert ids_first.isdisjoint(ids_second)
