"""SQLAlchemy model for AI-tailored resume versions."""

from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class TailoredResumeModel(Base):
    """ORM model storing tailored resume bullet points and export history."""

    __tablename__ = "tailored_resumes"

    resume_id: Mapped[str] = mapped_column(String(255), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    jd_id: Mapped[str | None] = mapped_column(String(255), ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Tailored Version")
    tailored_text: Mapped[str] = mapped_column(Text, nullable=False)
    bullet_changes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    improved_score: Mapped[float | None] = mapped_column(JSON, nullable=True)
