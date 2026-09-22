from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


engine = _make_engine(get_settings().database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def configure_database(database_url: str) -> None:
    """Reconfigure the database. Used by tests and explicit application setup."""
    global engine, SessionLocal
    engine.dispose()
    engine = _make_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    # Import models before metadata creation so every table is registered.
    from app.models import debug_session, execution_result  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Automatically migrate new columns for existing SQLite databases
    if engine.url.drivername.startswith("sqlite"):
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(debug_sessions);")).fetchall()
            existing_cols = {row[1] for row in result}
            new_columns = {
                "mode": "TEXT DEFAULT 'general'",
                "problem_statement": "TEXT DEFAULT ''",
                "constraints": "TEXT DEFAULT ''",
                "status": "TEXT DEFAULT 'completed'",
                "failure_type": "TEXT DEFAULT ''",
                "diff": "TEXT DEFAULT ''",
                "generated_tests_json": "TEXT DEFAULT '[]'",
                "iterations_json": "TEXT DEFAULT '[]'",
                "validation_json": "TEXT DEFAULT '{}'",
                "complexity_json": "TEXT DEFAULT '{}'",
            }
            for col_name, col_type in new_columns.items():
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE debug_sessions ADD COLUMN {col_name} {col_type};"))
            conn.commit()


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()

