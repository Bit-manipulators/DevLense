from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.execution.base import ExecutionUnavailable
from app.schemas.execution import ExecuteRequest, ExecuteResponse
from app.services.session_service import SessionNotFoundError, SessionService

router = APIRouter()


@router.post(
    "",
    response_model=ExecuteResponse,
    summary="Run code in the Docker sandbox",
    description="Executes Python, C++, or JavaScript only inside the constrained Docker sandbox.",
)
async def execute_code(
    payload: ExecuteRequest, request: Request, database: Session = Depends(get_db)
) -> ExecuteResponse:
    try:
        result = await request.app.state.execution_service.execute(
            payload.language, payload.code, payload.stdin
        )
    except ExecutionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        SessionService(database).save_execution(session_id=payload.session_id, **result.model_dump())
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Debug session not found.") from exc
    return ExecuteResponse(**result.model_dump())

