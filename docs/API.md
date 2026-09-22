# 📡 DevLens REST API Reference & Specification

> **Interactive API Explorer:** When the backend server is running, explore and test endpoints via Swagger UI at `http://localhost:8001/docs` or ReDoc at `http://localhost:8001/redoc`.

---

## 📑 Table of Contents

- [Overview & Base URL](#-overview--base-url)
- [Authentication & Rate Limiting](#-authentication--rate-limiting)
- [Common Headers & Status Codes](#-common-headers--status-codes)
- [Endpoints](#-endpoints)
  - [1. Code Analysis (`POST /api/v1/analyze`)](#1-code-analysis-post-apiv1analyze)
  - [2. Sandboxed Code Execution (`POST /api/v1/execute`)](#2-sandboxed-code-execution-post-apiv1execute)
  - [3. Intelligent Debug Engine (`POST /api/v1/debug`)](#3-intelligent-debug-engine-post-apiv1debug)
  - [4. OCR Code Capture (`POST /api/v1/ocr`)](#4-ocr-code-capture-post-apiv1ocr)
  - [5. AI Copilot Agent (`POST /api/v1/agent/chat`)](#5-ai-copilot-agent-post-apiv1agentchat)
  - [6. Session Management (`/api/v1/sessions`)](#6-session-management-apiv1sessions)
  - [7. Health & System Status (`GET /api/v1/health`)](#7-health--system-status-get-apiv1health)
- [Error Handling & Schema](#-error-handling--schema)

---

## 🌐 Overview & Base URL

* **Default Local Base URL:** `http://localhost:8001/api/v1`
* **Network / LAN URL:** `http://<YOUR_LAN_IP>:8001/api/v1`
* **Default Protocol:** HTTP/1.1 (HTTPS in production)
* **Default Content-Type:** `application/json` (except OCR multipart/form-data)

---

## 🔒 Authentication & Rate Limiting

* **Current Stage (MVP):** Public API endpoints with token-bucket client rate limiting enabled by default.
* **Rate Limits:** 60 requests/minute per client IP (customizable via `RATE_LIMIT_PER_MINUTE` in `.env`).
* **Rate Limit Headers:**
  * `X-RateLimit-Limit`: Maximum allowed requests per time window.
  * `X-RateLimit-Remaining`: Remaining request quota.
  * `X-RateLimit-Reset`: Unix epoch timestamp when quota resets.

---

## 📋 Common Headers & Status Codes

### Standard Response Headers
All API responses include security and caching headers:
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Cache-Control: no-store, no-cache, must-revalidate
```

### HTTP Status Codes

| Code | Meaning | Typical Scenario |
| :---: | :--- | :--- |
| `200 OK` | Request succeeded | Execution result, session retrieved, health check passed |
| `201 Created` | Resource created | Analysis created and session initialized |
| `204 No Content` | Action completed | Session deleted successfully |
| `400 Bad Request` | Client error | Malformed payload or unparseable input |
| `422 Unprocessable Entity` | Validation error | Missing required fields, oversized payload, unsupported language |
| `429 Too Many Requests` | Rate limited | Exceeded token-bucket quota |
| `503 Service Unavailable` | Service missing | Docker daemon offline when execution requested |
| `500 Internal Server Error` | Server error | Unexpected unhandled server exception |

---

## 🚀 Endpoints

### 1. Code Analysis (`POST /api/v1/analyze`)

Analyzes submitted source code for syntax errors, logical bugs, edge cases, and anti-patterns using multi-language rule engines with optional Ollama LLM fallback.

* **Endpoint:** `/api/v1/analyze`
* **Method:** `POST`
* **Content-Type:** `application/json`

#### Request Body
```json
{
  "language": "python",
  "code": "def find_max(arr):\n    max_val = arr[0]\n    for i in range(len(arr)):\n        if arr[i] > max_val:\n            max_val = arr[i]\n    return max_val\n",
  "error_message": "IndexError: list index out of range",
  "question": "Why does this fail on empty lists?"
}
```

| Field | Type | Required | Description | Constraints |
| :--- | :---: | :---: | :--- | :--- |
| `language` | `string` | Yes | Programming language identifier (`python`, `javascript`, `cpp`, `java`) | Supported enum |
| `code` | `string` | Yes | Source code to inspect | 1 to 50,000 characters |
| `error_message` | `string` | No | Optional runtime error trace or compiler output | Max 20,000 characters |
| `question` | `string` | No | Specific developer inquiry | Max 4,000 characters |

#### Response (`201 Created`)
```json
{
  "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "created_at": "2026-09-22T14:30:00Z",
  "language": "python",
  "code": "def find_max(arr):\n    max_val = arr[0]\n...",
  "finding": {
    "severity": "high",
    "root_cause": "Unhandled empty collection access",
    "explanation": "Accessing arr[0] without verifying array length raises IndexError on empty inputs.",
    "affected_lines": [2],
    "suggested_fix": "def find_max(arr):\n    if not arr:\n        return None\n    max_val = arr[0]\n    for i in range(1, len(arr)):\n        if arr[i] > max_val:\n            max_val = arr[i]\n    return max_val\n",
    "debugging_steps": [
      "Check if input list is non-empty before indexing.",
      "Handle edge cases such as empty lists gracefully."
    ],
    "confidence": 0.95
  }
}
```

---

### 2. Sandboxed Code Execution (`POST /api/v1/execute`)

Compiles and executes code inside a zero-trust ephemeral Docker container with strict resource, network, and capability limits.

* **Endpoint:** `/api/v1/execute`
* **Method:** `POST`
* **Content-Type:** `application/json`

#### Request Body
```json
{
  "language": "python",
  "code": "import sys\nname = sys.stdin.read().strip()\nprint(f'Hello, {name}!')",
  "stdin": "DevLens User",
  "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

| Field | Type | Required | Description |
| :--- | :---: | :---: | :--- |
| `language` | `string` | Yes | Target language (`python`, `javascript`, `cpp`, `java`) |
| `code` | `string` | Yes | Source code to execute |
| `stdin` | `string` | No | Optional standard input string (max 10 KB) |
| `session_id` | `string` | No | Optional UUID of associated debug session |

#### Response (`200 OK`)
```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "Hello, DevLens User!\n",
  "stderr": "",
  "duration_ms": 142.5,
  "timed_out": false,
  "truncated": false,
  "error_type": null
}
```

#### Error Response when Docker is unavailable (`503 Service Unavailable`)
```json
{
  "detail": "Docker sandbox is unavailable on the server."
}
```

---

### 3. Intelligent Debug Engine (`POST /api/v1/debug`)

Executes an iterative, multi-stage debugging pipeline (Problem Ingestion $\to$ Static Diagnostics $\to$ Sandboxed Verification $\to$ Test Case Synthesis $\to$ Automated Repair $\to$ Complexity Analysis).

* **Endpoint:** `/api/v1/debug`
* **Method:** `POST`
* **Content-Type:** `application/json`

#### Request Body
```json
{
  "mode": "leetcode",
  "language": "python",
  "problem_statement": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
  "constraints": "2 <= nums.length <= 10^4",
  "code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n",
  "test_cases": [
    { "input": "nums = [2,7,11,15], target = 9", "output": "[0,1]" },
    { "input": "nums = [3,2,4], target = 6", "output": "[1,2]" }
  ]
}
```

#### Response (`200 OK`)
```json
{
  "session_id": "8f394c20-d092-416b-9c71-f925f46bb71b",
  "status": "fixed",
  "language": "python",
  "problem_summary": "Two Sum (Array Archetype)",
  "root_cause": "Identical index pairing and O(N^2) brute-force nested loop",
  "failure_type": "wrong_answer",
  "evidence": [
    {
      "test_case": "nums=[3,2,4], target=6",
      "expected": "[1, 2]",
      "actual": "[0, 0]",
      "category": "logic_failure"
    }
  ],
  "original_code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n",
  "corrected_code": "def twoSum(nums, target):\n    lookup = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in lookup:\n            return [lookup[complement], i]\n        lookup[num] = i\n    return []\n",
  "diff": "--- Original\n+++ Repaired\n@@ -1,5 +1,7 @@\n def twoSum(nums, target):\n-    for i in range(len(nums)):\n-        for j in range(len(nums)):\n-            if nums[i] + nums[j] == target:\n-                return [i, j]\n+    lookup = {}\n+    for i, num in enumerate(nums):\n+        complement = target - num\n+        if complement in lookup:\n+            return [lookup[complement], i]\n+        lookup[num] = i\n+    return []\n",
  "affected_lines": [2, 3, 4, 5],
  "iterations": [
    {
      "iteration": 1,
      "diagnosis": "Inner loop compares index with itself and violates distinct element constraint.",
      "suggested_fix": "Use a hash map complement lookup in a single pass.",
      "diff": "...",
      "tests_passed": 2,
      "tests_failed": 0,
      "validated": true
    }
  ],
  "tests_run": 2,
  "tests_passed": 2,
  "tests_failed": 0,
  "validation": {
    "compile": true,
    "runtime": true,
    "tests": true
  },
  "complexity": {
    "time_complexity": "O(N)",
    "space_complexity": "O(N)",
    "explanation": "Single-pass hash table lookup achieves optimal linear time complexity."
  }
}
```

---

### 4. OCR Code Capture (`POST /api/v1/ocr`)

Processes image data (from device camera or photo gallery) in-memory, extracts text, cleans up OCR anomalies, and automatically detects programming language.

* **Endpoint:** `/api/v1/ocr`
* **Method:** `POST`
* **Content-Type:** `multipart/form-data` or `application/json` (Base64)

#### Form Data Payload
* `file`: Image binary (`image/jpeg`, `image/png`, `image/webp`)

#### JSON Payload Alternative
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "hint_language": "python"
}
```

#### Response (`200 OK`)
```json
{
  "extracted_code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "detected_language": "python",
  "confidence_score": 0.94,
  "warnings": []
}
```

---

### 5. AI Copilot Agent (`POST /api/v1/agent/chat`)

Conversational agent that inspects workspace code, answers debugging queries, generates unit tests, and explains complex algorithms.

* **Endpoint:** `/api/v1/agent/chat`
* **Method:** `POST`
* **Content-Type:** `application/json`

#### Request Body
```json
{
  "prompt": "How can I optimize this loop to run in linear time?",
  "code": "def has_duplicate(arr):\n    for i in range(len(arr)):\n        for j in range(i+1, len(arr)):\n            if arr[i] == arr[j]: return True\n    return False",
  "language": "python",
  "history": []
}
```

#### Response (`200 OK`)
```json
{
  "response": "You can achieve O(N) time complexity by using a hash set to track seen elements in a single pass.",
  "suggested_code": "def has_duplicate(arr):\n    seen = set()\n    for item in arr:\n        if item in seen:\n            return True\n        seen.add(item)\n    return False",
  "actions": [
    { "type": "replace_code", "label": "Apply Set-based Optimization" }
  ]
}
```

---

### 6. Session Management (`/api/v1/sessions`)

Persists, retrieves, and organizes developer debugging sessions.

#### A. List Sessions (`GET /api/v1/sessions`)
* **Query Parameters:**
  * `limit` (integer, default: 50, max: 100): Number of records to return.
  * `offset` (integer, default: 0): Pagination offset.
* **Response (`200 OK`):**
```json
[
  {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "created_at": "2026-09-22T14:30:00Z",
    "language": "python",
    "severity": "high",
    "root_cause": "Unhandled empty collection access",
    "preview_code": "def find_max(arr):..."
  }
]
```

#### B. Get Session Details (`GET /api/v1/sessions/{session_id}`)
* **Path Parameter:** `session_id` (UUID string)
* **Response (`200 OK`):** Returns full session record including `finding`, `executions`, and `debug_report`.

#### C. Delete Session (`DELETE /api/v1/sessions/{session_id}`)
* **Path Parameter:** `session_id` (UUID string)
* **Response (`204 No Content`):** Confirms permanent deletion.

---

### 7. Health & System Status (`GET /api/v1/health`)

Queries API availability, database connectivity, and Docker sandbox status.

* **Endpoint:** `/api/v1/health`
* **Method:** `GET`

#### Response (`200 OK`)
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "docker_sandbox": {
    "available": true,
    "version": "27.2.0",
    "supported_languages": ["python", "javascript", "cpp", "java"]
  },
  "ai_provider": {
    "configured": "rule_based",
    "ollama_available": false
  }
}
```

---

## ⚠️ Error Handling & Schema

When a request validation fails or an exception occurs, DevLens returns a structured error object conforming to RFC 7807:

```json
{
  "error": "Validation Error",
  "detail": [
    {
      "loc": ["body", "language"],
      "msg": "Input should be 'python', 'javascript', 'cpp' or 'java'",
      "type": "enum"
    }
  ],
  "status_code": 422
}
```
