from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.analyzers.factory import get_analyzer
from app.api.router import api_router
from app.config import get_settings
from app.database import init_db
from app.execution.hybrid import HybridExecutionService
from app.services.analysis_service import AnalysisService
from app.utils.rate_limit import InMemoryRateLimiter

logger = logging.getLogger("devlens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    app.state.settings = settings
    app.state.analysis_service = AnalysisService(get_analyzer(settings))
    app.state.execution_service = HybridExecutionService(settings)
    app.state.rate_limiter = InMemoryRateLimiter(settings.max_requests_per_minute)
    yield


app = FastAPI(
    title="DevLens API",
    version="0.1.0",
    description="Secure, mobile-first code analysis and Docker-sandboxed execution.",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def security_and_rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        client_key = request.client.host if request.client else "unknown"
        limiter = getattr(request.app.state, "rate_limiter", None)
        if limiter and not limiter.allow(client_key):
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please retry shortly."})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Validation details are useful to clients but never expose server internals.
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled DevLens API error")
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})


app.include_router(api_router)


@app.get("/", summary="Root status", tags=["Root"])
async def root():
    return {
        "status": "ok",
        "service": "DevLens API",
        "version": app.version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
