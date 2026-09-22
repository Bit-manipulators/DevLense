from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.languages.registry import UnsupportedLanguageError
from app.schemas.debug import DebugReport, DebugRequest
from app.services.session_service import SessionService

router = APIRouter()


@router.post(
    "",
    response_model=DebugReport,
    status_code=status.HTTP_200_OK,
    summary="Evidence-driven code debugging pipeline",
    description="Orchestrates problem understanding, static & complexity analysis, sandboxed execution, test generation, failure diagnosis, repair, and verification.",
)
async def debug_code(
    payload: DebugRequest,
    request: Request,
    database: Session = Depends(get_db),
) -> DebugReport:
    orchestrator = request.app.state.debug_orchestrator
    try:
        report = await orchestrator.debug(payload)
    except UnsupportedLanguageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Persist session with full debug metadata
    session_item = SessionService(database).create_debug_session(
        request=payload,
        report=report,
    )
    report.session_id = session_item.id

    return report
