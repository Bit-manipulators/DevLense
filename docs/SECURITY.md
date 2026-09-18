# Security architecture and threat model

## Security position

DevLens allows untrusted code submission but never treats that code as safe. The API process does not run submitted code locally. Docker execution is deliberately unavailable rather than downgraded to host execution when Docker is missing.

## Controls

- Pydantic validation bounds source at 50 KB, stack traces at 20 KB, stdin at 10 KB, and questions at 4 KB.
- Docker uses fixed command arguments, no network, read-only root, temporary workspace, capped CPU/memory/PIDs, dropped capabilities, no-new-privileges, timeout kill, and output truncation.
- CORS is an explicit configurable allow-list. Responses include `nosniff`, frame denial, no-referrer, and no-store headers.
- The in-memory limiter is an MVP abstraction. Deployments should replace it with shared Redis-backed limits before scaling.
- Environment configuration contains no credentials by default. Errors returned to clients are sanitized; internal errors are logged server-side.
- Ollama prompts mark submitted code/comments as data, not instructions. Model output is schema-validated before use.

## Threats and mitigations

| Threat | Mitigation | Residual risk |
| --- | --- | --- |
| Malicious source / host command injection | No host shell interpolation; Docker-only execution | Docker daemon and images must be patched |
| Fork bomb / process flood | PID limit, timeout, CPU cap | A dedicated runner host is required at scale |
| Infinite loop | API wait timeout and container termination | Queued tasks still consume resources until killed |
| Memory exhaustion | Container memory cap | Kernel/container runtime configuration matters |
| Filesystem access | Read-only root and isolated temporary mount | Mount only the execution workspace |
| Network exfiltration | `--network none` | Validate Docker policy in deployment |
| Oversized input/output | API field limits and output cap | Reverse proxy body limits should also be set |
| Prompt injection in code/comments | Treat code as data; local analyzer works without LLM; constrained JSON schema | LLM findings are advisory, not authority |

## Deployment requirements

Use an authenticated API gateway, HTTPS, per-user quotas, audit logging with redaction, centralized rate limiting, dependency scanning, and a dedicated ephemeral runner fleet. Do not expose a Docker socket to an untrusted API process. Do not run this local MVP as a multi-tenant internet code-execution platform without those controls.

