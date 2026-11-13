"""SQLAlchemy database setup — SQLite at the resolved data directory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from jncep_webui.paths import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    """Create all tables if they don't exist (idempotent)."""
    from .models import Base  # noqa: PLC0415 — avoid circular import at module level

    Base.metadata.create_all(engine)


def get_session() -> Session:
    """Return a new SQLAlchemy session. Caller must close it."""
    return Session(engine)
