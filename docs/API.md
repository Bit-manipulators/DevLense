# API reference

The running backend also exposes interactive OpenAPI documentation at `/docs`.

## Analyze

`POST /api/v1/analyze`

```json
{
  "language": "cpp",
  "code": "int values[5]; for (int i = 0; i <= 5; i++) values[i] = i;",
  "error_message": "Segmentation fault",
  "question": "Why does this crash?"
}
```

It returns a session ID and structured finding: severity, root cause, explanation, affected lines, suggested/corrected code, debugging steps, and a 0–1 confidence score.

## Execute

`POST /api/v1/execute`

```json
{
  "language": "python",
  "code": "print(input())",
  "stdin": "hello",
  "session_id": "optional-debug-session-id"
}
```

Only `python`, `cpp`, and `javascript` are executable. A missing Docker sandbox yields HTTP 503. A compilation or program failure returns HTTP 200 with `success: false`, plus compiler/runtime stderr and its exit code.

## Debug Engine

`POST /api/v1/debug`

Orchestrates the complete evidence-driven debugging pipeline (problem understanding, multi-layer static & complexity analysis, sandboxed execution, test generation, failure analysis, repair, and verification).

```json
{
  "mode": "leetcode",
  "language": "python",
  "problem_statement": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
  "constraints": "2 <= nums.length <= 10^4",
  "code": "def twoSum(nums, target):\n    # implementation\n",
  "test_cases": [
    {"input": "nums = [3,3], target = 6", "output": "[0,1]"}
  ]
}
```

Response returns a complete `DebugReport` including status (`fixed`, `failed`, `passed`, `needs_review`), root cause, failure type, concrete failure evidence, unified diff, affected lines, iteration records, test metrics, validation summary (compile, runtime, tests), and complexity analysis ($O(N)$, $O(N^2)$, etc.).

## Sessions

- `GET /api/v1/sessions` returns session summaries newest first.
- `GET /api/v1/sessions/{session_id}` returns the full saved analysis, including debug metadata if initiated via the debugging engine.
- `DELETE /api/v1/sessions/{session_id}` returns 204 after removal.

Invalid fields, blank code, unsupported languages, and oversized payloads are rejected with HTTP 422. Each API response carries basic security headers and no-store cache control.

