# Development guide

## Daily workflow

1. Start the backend from `backend` with `uvicorn app.main:app --reload --host 0.0.0.0 --port 8001`.
2. Copy `mobile/.env.example` to `mobile/.env` and set the backend LAN URL for physical-device testing.
3. Start Expo from `mobile` with `npx expo start`.
4. Use one of the included real demo inputs to confirm analysis and persistence.

## Tests

- Backend: `python -m pytest -q`.
- Mobile: `npm test` and `npm run typecheck`.

This sandboxed development environment prevents pytest from using its normal global temporary directory, so the verified command used `python -m pytest -q --basetemp=.pytest-tmp`. On a normal local developer machine the standard command is sufficient.

## Rules for contributors

- Keep API calls inside `mobile/services/api.ts`.
- Keep untrusted code out of host shell commands and avoid expanding execution permissions.
- Add analyzer rules with precise language and calibrated confidence; do not claim proof where a heuristic only indicates risk.
- Keep nonfunctional future capabilities out of primary product flows.
