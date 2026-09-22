from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.session_service import SessionService

router = APIRouter()


@router.post(
    "",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze source code",
    description="Runs the configured analyzer and persists a debugging session.",
)
async def analyze_code(
    payload: AnalyzeRequest, request: Request, database: Session = Depends(get_db)
) -> AnalyzeResponse:
    finding = await request.app.state.analysis_service.analyze(
        payload.language, payload.code, payload.error_message, payload.question
    )
    item = SessionService(database).create_session(
        language=payload.language,
        code=payload.code,
        error_message=payload.error_message,
        question=payload.question,
        finding=finding,
    )
    return AnalyzeResponse(session_id=item.id, language=item.language, **finding.model_dump())

