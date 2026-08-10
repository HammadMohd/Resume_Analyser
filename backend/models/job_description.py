"""SQLAlchemy model for job descriptions."""

from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class JobDescriptionModel(Base):
    """ORM model storing job description title, text, and extracted requirements."""

    __tablename__ = "job_descriptions"

    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
