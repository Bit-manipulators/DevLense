from fastapi import APIRouter

from app.api.routes import analysis, execution, health, ocr, sessions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
api_router.include_router(execution.router, prefix="/execute", tags=["Execution"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR"])

