from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.analyzers.base import AnalysisFinding
from app.models.debug_session import DebugSession
from app.models.execution_result import ExecutionResult


class SessionNotFoundError(LookupError):
    pass


class SessionService:
    def __init__(self, database: Session):
        self.database = database

    def create_session(
        self,
        *,
        language: str,
        code: str,
        error_message: str,
        question: str,
        finding: AnalysisFinding,
    ) -> DebugSession:
        item = DebugSession(
            language=language,
            code=code,
            error_message=error_message,
            question=question,
            summary=finding.summary,
            severity=finding.severity,
            root_cause=finding.root_cause,
            explanation=finding.explanation,
            affected_lines_json=json.dumps(finding.affected_lines),
            suggested_fix=finding.suggested_fix,
            corrected_code=finding.corrected_code,
            debugging_steps_json=json.dumps(finding.debugging_steps),
            confidence=finding.confidence,
        )
        self.database.add(item)
        self.database.commit()
        self.database.refresh(item)
        return item

    def create_debug_session(
        self,
        *,
        request: Any,
        report: Any,
    ) -> DebugSession:
        item = DebugSession(
            language=report.language,
            code=report.original_code,
            error_message=getattr(request, "error_message", "") or "",
            question=getattr(request, "question", "") or "",
            summary=report.problem_summary or "Debug Session",
            severity="high" if report.status in ("failed", "needs_review") else "medium",
            root_cause=report.root_cause,
            explanation=f"Status: {report.status}. Failure type: {report.failure_type}.",
            affected_lines_json=json.dumps(report.affected_lines),
            suggested_fix=report.iterations[-1].suggested_fix if report.iterations else "See debug report",
            corrected_code=report.corrected_code,
            debugging_steps_json=json.dumps([f"Ran {report.tests_run} tests: {report.tests_passed} passed, {report.tests_failed} failed."]),
            confidence=0.95 if report.status in ("fixed", "passed") else 0.5,
            mode=getattr(request, "mode", "general"),
            problem_statement=getattr(request, "problem_statement", ""),
            constraints=getattr(request, "constraints", ""),
            status=report.status,
            failure_type=report.failure_type,
            diff=report.diff,
            generated_tests_json=json.dumps([e.model_dump() for e in report.evidence]),
            iterations_json=json.dumps([it.model_dump() for it in report.iterations]),
            validation_json=json.dumps(report.validation.model_dump()),
            complexity_json=json.dumps(report.complexity.model_dump()),
        )
        self.database.add(item)
        self.database.commit()
        self.database.refresh(item)
        return item

    def list_sessions(self, limit: int = 50, offset: int = 0) -> list[DebugSession]:
        statement = (
            select(DebugSession)
            .options(selectinload(DebugSession.execution_results))
            .order_by(DebugSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.database.scalars(statement))

    def get_session(self, session_id: str) -> DebugSession:
        item = self.database.get(DebugSession, session_id)
        if item is None:
            raise SessionNotFoundError(session_id)
        return item

    def delete_session(self, session_id: str) -> None:
        item = self.get_session(session_id)
        self.database.delete(item)
        self.database.commit()

    def save_execution(
        self,
        *,
        session_id: str | None,
        success: bool,
        stdout: str,
        stderr: str,
        exit_code: int,
        execution_time_ms: int,
    ) -> ExecutionResult:
        if session_id:
            self.get_session(session_id)
        result = ExecutionResult(
            session_id=session_id,
            success=success,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time_ms=execution_time_ms,
        )
        self.database.add(result)
        self.database.commit()
        self.database.refresh(result)
        return result

