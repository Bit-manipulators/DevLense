from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DebugSession(Base):
    __tablename__ = "debug_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    language: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    question: Mapped[str] = mapped_column(Text, default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    affected_lines_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_code: Mapped[str] = mapped_column(Text, nullable=False)
    debugging_steps_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), default="general", nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, default="", nullable=False)
    constraints: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    failure_type: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    diff: Mapped[str] = mapped_column(Text, default="", nullable=False)
    generated_tests_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    iterations_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    validation_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    complexity_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    execution_results: Mapped[list["ExecutionResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
