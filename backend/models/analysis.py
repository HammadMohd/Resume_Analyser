"""SQLAlchemy model for resume ATS analysis results."""

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class AnalysisModel(Base):
    """ORM model storing ATS score, multi-ATS breakdown, and validation feedback."""

    __tablename__ = "analyses"

    resume_id: Mapped[str] = mapped_column(String(255), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    jd_id: Mapped[str | None] = mapped_column(String(255), ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(10), nullable=False)
    
    category_scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    ats_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
