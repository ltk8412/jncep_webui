"""SQLAlchemy ORM models for download history tracking."""

# pyright: reportUninitializedInstanceVariable=false

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class DownloadHistory(Base):
    """Tracks every EPUB generation with series info and job status."""

    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    jnovelclub_url: Mapped[str]
    prepub_parts: Mapped[str]
    output_filenames: Mapped[str]
    saved_to_server: Mapped[bool]
    downloaded_to_client: Mapped[bool]
    status: Mapped[str] = mapped_column(default="completed")
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
