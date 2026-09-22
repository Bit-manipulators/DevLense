from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.debug_session import DebugSession
from app.schemas.sessions import SessionDetail, SessionExecutionItem, SessionListItem
from app.services.session_service import SessionNotFoundError, SessionService

router = APIRouter()


def _detail(item: DebugSession) -> SessionDetail:
    return SessionDetail(
        id=item.id,
        language=item.language,
        code=item.code,
        error_message=item.error_message,
        question=item.question,
        summary=item.summary,
        severity=item.severity,
        root_cause=item.root_cause,
        explanation=item.explanation,
        affected_lines=json.loads(item.affected_lines_json),
        suggested_fix=item.suggested_fix,
        corrected_code=item.corrected_code,
        debugging_steps=json.loads(item.debugging_steps_json),
        confidence=item.confidence,
        mode=getattr(item, "mode", "general"),
        status=getattr(item, "status", "completed"),
        diff=getattr(item, "diff", ""),
        problem_statement=getattr(item, "problem_statement", ""),
        constraints=getattr(item, "constraints", ""),
        failure_type=getattr(item, "failure_type", ""),
        execution_count=len(item.execution_results),
        created_at=item.created_at,
        execution_history=[
            SessionExecutionItem(
                id=res.id,
                success=res.success,
                stdout=res.stdout,
                stderr=res.stderr,
                exit_code=res.exit_code,
                execution_time_ms=res.execution_time_ms,
                created_at=res.created_at,
            )
            for res in sorted(item.execution_results, key=lambda r: r.created_at, reverse=True)
        ],
    )


@router.get("", response_model=list[SessionListItem], summary="List debugging sessions")
def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    database: Session = Depends(get_db),
) -> list[SessionListItem]:
    return [
        SessionListItem(
            id=item.id,
            language=item.language,
            summary=item.summary,
            severity=item.severity,
            confidence=item.confidence,
            execution_count=len(item.execution_results),
            created_at=item.created_at,
        )
        for item in SessionService(database).list_sessions(limit=limit, offset=offset)
    ]


@router.get("/{session_id}", response_model=SessionDetail, summary="Get a debugging session")
def get_session(session_id: str, database: Session = Depends(get_db)) -> SessionDetail:
    try:
        return _detail(SessionService(database).get_session(session_id))
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Debug session not found.") from exc


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a debugging session")
def delete_session(session_id: str, database: Session = Depends(get_db)) -> Response:
    try:
        SessionService(database).delete_session(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Debug session not found.") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
