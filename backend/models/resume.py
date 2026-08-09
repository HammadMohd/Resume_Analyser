"""SQLAlchemy model for stored resume documents."""

from typing import Any

from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class ResumeModel(Base):
    """ORM model storing resume metadata, parsed content, and raw text."""

    __tablename__ = "resumes"

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extracted_entities: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
