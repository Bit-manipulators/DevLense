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


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()

