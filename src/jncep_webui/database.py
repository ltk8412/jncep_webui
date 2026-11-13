"""SQLAlchemy database setup — SQLite at the resolved data directory."""

import sqlite3

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import ConnectionPoolEntry

from jncep_webui.paths import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}")


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(
    dbapi_connection: sqlite3.Connection,
    _connection_record: ConnectionPoolEntry,
) -> None:
    """Enable WAL so background download jobs and request threads can use the DB concurrently.

    Executed on the raw DBAPI connection so the PRAGMA result row is discarded
    with the cursor instead of corrupting the SQLAlchemy connection state.

    """
    cursor = dbapi_connection.cursor()
    _ = cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def init_db() -> None:
    """Create all tables if they don't exist (idempotent), then migrate columns."""
    from .models import Base  # noqa: PLC0415 — avoid circular import at module level

    Base.metadata.create_all(engine)
    _migrate_columns()


def _migrate_columns() -> None:
    """Add columns introduced after the original schema to existing SQLite tables."""
    migrations = {
        "status": "VARCHAR NOT NULL DEFAULT 'completed'",
        "error_message": "VARCHAR",
    }
    with engine.connect() as connection:
        existing = {
            row[1]
            for row in connection.execute(
                text("PRAGMA table_info(download_history)"),
            )
        }
        for column, ddl in migrations.items():
            if column not in existing:
                _ = connection.execute(
                    text(f"ALTER TABLE download_history ADD COLUMN {column} {ddl}"),
                )
        connection.commit()


def get_session() -> Session:
    """Return a new SQLAlchemy session. Caller must close it."""
    return Session(engine)
