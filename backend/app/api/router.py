from fastapi import APIRouter

from app.api.routes import agent, analysis, debug, execution, health, ocr, sessions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(debug.router, prefix="/debug", tags=["Debug"])
api_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
api_router.include_router(execution.router, prefix="/execute", tags=["Execution"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])

