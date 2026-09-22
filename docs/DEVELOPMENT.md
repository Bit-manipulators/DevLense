# 🛠️ DevLens Developer & Contributor Guide

Welcome to the DevLens development ecosystem! This guide provides all necessary instructions, environment setups, testing workflows, and conventions to contribute to both the FastAPI backend and Expo React Native mobile application.

---

## 📑 Table of Contents

- [1. Prerequisites & Environment Setup](#1-prerequisites--environment-setup)
- [2. Backend Development Workflow (FastAPI)](#2-backend-development-workflow-fastapi)
- [3. Frontend Development Workflow (Expo / React Native)](#3-frontend-development-workflow-expo--react-native)
- [4. Connecting Mobile to Local Backend](#4-connecting-mobile-to-local-backend)
- [5. Step-by-Step: Adding a New Language Analyzer](#5-step-by-step-adding-a-new-language-analyzer)
- [6. Testing & Quality Assurance](#6-testing--quality-assurance)
- [7. Troubleshooting & FAQ](#7-troubleshooting--faq)
- [8. Code Style & Contribution Conventions](#8-code-style--contribution-conventions)

---

## 1. Prerequisites & Environment Setup

Ensure you have the following installed on your development machine:

| Component | Minimum Version | Recommended | Purpose |
| :--- | :---: | :---: | :--- |
| **Python** | 3.12+ | 3.12 / 3.13 | Backend API, analysis engine, testing |
| **Node.js** | 20.x LTS | 20.14+ | Expo React Native tooling & frontend |
| **npm** | 10.x+ | Latest | JavaScript package management |
| **Docker Desktop** | 24.0+ | Latest | Ephemeral sandbox execution engine |
| **Git** | 2.40+ | Latest | Version control |
| **Expo Go (Mobile)** | SDK 51/54 | Latest | Mobile preview on physical smartphone |

---

## 2. Backend Development Workflow (FastAPI)

The backend is housed in [`backend/`](../backend).

### 2.1 Initialization

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create environment configuration
cp .env.example .env

# 3. Create and activate Python virtual environment
# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt
```

### 2.2 Environment Variables (`.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./devlens.db` | SQLAlchemy asynchronous database connection string |
| `ANALYZER_PROVIDER` | `rule_based` | `rule_based` (default) or `ollama` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Endpoint for Ollama local LLM instance |
| `OLLAMA_MODEL` | `llama3:8b` | Model name for AI code diagnostics |
| `RATE_LIMIT_PER_MINUTE` | `60` | Client IP rate limit window |
| `DOCKER_TIMEOUT_SECONDS`| `5` | Maximum execution time before container termination |

### 2.3 Starting the Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

* 🚀 **API Home:** `http://localhost:8001`
* 📚 **Interactive Swagger API Docs:** `http://localhost:8001/docs`
* 🩺 **Health Check:** `http://localhost:8001/api/v1/health`

---

## 3. Frontend Development Workflow (Expo / React Native)

The mobile and web client is housed in [`mobile/`](../mobile).

### 3.1 Initialization

```bash
# 1. Navigate to mobile directory
cd mobile

# 2. Create environment configuration
cp .env.example .env

# 3. Install dependencies
npm install
```

### 3.2 Starting the Expo Bundler

```bash
npx expo start
```

* **Web Browser:** Press `w` in the terminal to launch the web client at `http://localhost:8081`.
* **Android Emulator:** Press `a` (requires Android Studio & running AVD).
* **iOS Simulator:** Press `i` (requires macOS & Xcode).
* **Physical Device:** Scan the QR code using the **Expo Go** mobile app.

---

## 4. Connecting Mobile to Local Backend

When testing on a physical smartphone, the mobile app needs to reach your computer's backend API.

### Option A: Wi-Fi LAN Bridge (Recommended)
1. Ensure your PC and phone are connected to the **same Wi-Fi network**.
2. Find your computer's local IPv4 address:
   - **Linux/macOS:** `ifconfig` or `ip a` (e.g., `192.168.1.15`)
   - **Windows:** `ipconfig`
3. Update `mobile/.env`:
   ```env
   EXPO_PUBLIC_API_URL=http://192.168.1.15:8001
   ```
4. Restart Expo bundler: `npx expo start -c`

### Option B: High-Speed USB Reverse Tunnel (Android ADB)
If testing via USB cable with developer mode enabled:
```bash
adb reverse tcp:8001 tcp:8001
```
Now `http://localhost:8001` on your phone resolves directly to your development PC.

---

## 5. Step-by-Step: Adding a New Language Analyzer

DevLens uses an extensible modular analyzer architecture. To add support for a new language (e.g., `Rust` or `Go`):

### Step 1: Create Language Rule Parser
Create a new file in `backend/app/analyzers/languages/rust.py`:

```python
from app.analyzers.base import BaseLanguageRule
from app.schemas.analysis import AnalysisFinding

class RustRuleAnalyzer(BaseLanguageRule):
    language = "rust"

    def analyze(self, code: str, error_message: str | None = None) -> AnalysisFinding | None:
        # 1. Check for unwrap() on None/Err
        if ".unwrap()" in code and ("panic" in (error_message or "").lower() or "NoneError" in (error_message or "")):
            return AnalysisFinding(
                severity="high",
                root_cause="Unchecked unwrap() panic",
                explanation="Calling .unwrap() on an Option::None or Result::Err triggers an unhandled panic.",
                affected_lines=[self._find_line(code, ".unwrap()")],
                suggested_fix=code.replace(".unwrap()", ".unwrap_or_default()"),
                debugging_steps=[
                    "Use match or if let to handle Option/Result safely.",
                    "Use .unwrap_or() or .expect() with descriptive errors."
                ],
                confidence=0.92
            )
        return None
```

### Step 2: Register in Analyzer Factory
Add the new parser to [`backend/app/analyzers/factory.py`](../backend/app/analyzers/factory.py).

### Step 3: Add Docker Sandbox Runtime (Optional)
If sandboxed execution is supported, add the Docker image to [`backend/app/execution/manager.py`](../backend/app/execution/manager.py):
```python
SUPPORTED_CONTAINERS = {
    "python": "python:3.12-alpine",
    "javascript": "node:20-alpine",
    "cpp": "gcc:14.2.0",
    "java": "eclipse-temurin:21-alpine",
    "rust": "rust:1.80-alpine",
}
```

### Step 4: Write Unit Tests
Add test cases in `backend/tests/` to verify rule triggers, execution adapters, and confidence accuracy.

---

## 6. Testing & Quality Assurance

### 6.1 Backend Test Suite (Pytest)
The backend test suite contains **59 tests across 12 modules** ensuring 100% pass rates across evidence-driven debugging, live compilation, and OCR pipelines:

```bash
cd backend

# Run all 59 tests
python -m pytest -v

# Run specific test suites
python -m pytest tests/test_debug_api.py -v
python -m pytest tests/test_live_execution.py -v
python -m pytest tests/test_benchmarks.py -v
python -m pytest tests/test_ocr.py -v
```

### 6.2 Mobile Test Suite & TypeScript Verification (Jest)
The mobile client contains **17 tests across 5 Jest test suites**:

```bash
cd mobile

# Run Jest unit tests (17 passing tests)
npm test

# Run TypeScript typecheck (0 errors)
npm run typecheck
```

---

## 7. Troubleshooting & FAQ

### Q1: `Docker sandbox is unavailable on the server`
* **Behavior:** DevLens automatically falls back to the **Process Jail** sandbox. If Docker is desired, ensure Docker Desktop or `dockerd` is running.
* **Fix:** Start Docker Desktop. On Linux, ensure your user is in the `docker` group (`sudo usermod -aG docker $USER`).

### Q2: Phone cannot reach API (`Network request failed`)
* **Cause:** Firewall blocking port 8001 or incorrect LAN IP address.
* **Fix:** Verify firewall allows incoming connections on port 8001. Ensure both devices share the exact same subnet, or use USB ADB reverse tunneling (`adb reverse tcp:8001 tcp:8001`).

### Q3: Metro Bundler shows stale code
* **Fix:** Clear cache by starting with `npx expo start -c`.

---

## 8. Code Style & Contribution Conventions

* **Typing:** Strict typing is enforced in both Python (Pydantic / Type annotations) and TypeScript.
* **API Contracts:** All client-side HTTP calls must be centralized in [`mobile/services/api.ts`](../mobile/services/api.ts).
* **Heuristic Integrity:** Rule analyzers must only produce findings with calibrated confidence scores (0.0 to 1.0) and must never claim certainty on speculative heuristics.
* **Security Guardrails:** Never introduce shell string concatenation or bypass container execution sandboxes.
