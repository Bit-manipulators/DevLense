from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExecutionResult(Base):
    __tablename__ = "execution_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("debug_sessions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    success: Mapped[bool] = mapped_column(nullable=False)
    stdout: Mapped[str] = mapped_column(Text, default="", nullable=False)
    stderr: Mapped[str] = mapped_column(Text, default="", nullable=False)
    exit_code: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    session: Mapped["DebugSession | None"] = relationship(back_populates="execution_results")
