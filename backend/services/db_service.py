"""Database service module providing async CRUD operations for resumes and analysis."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.analysis import AnalysisModel
from backend.models.job_description import JobDescriptionModel
from backend.models.resume import ResumeModel
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """Service encapsulating database persistence logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_resume(
        self,
        original_filename: str,
        stored_filename: str,
        content_type: str,
        size_bytes: int,
        raw_text: str | None = None,
        parsed_data: dict[str, Any] | None = None,
        extracted_entities: dict[str, Any] | None = None,
    ) -> ResumeModel:
        """Create and store a resume record."""
        resume = ResumeModel(
            id=str(uuid.uuid4()),
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            raw_text=raw_text,
            parsed_data=parsed_data,
            extracted_entities=extracted_entities,
        )
        self.session.add(resume)
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def create_job_description(
        self,
        raw_text: str,
        title: str = "",
        company: str | None = None,
        extracted_data: dict[str, Any] | None = None,
    ) -> JobDescriptionModel:
        """Create and store a job description record."""
        jd = JobDescriptionModel(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            raw_text=raw_text,
            extracted_data=extracted_data,
        )
        self.session.add(jd)
        await self.session.commit()
        await self.session.refresh(jd)
        return jd

    async def save_analysis(
        self,
        resume_id: str,
        overall_score: float,
        grade: str,
        category_scores: dict[str, Any],
        ats_breakdown: dict[str, Any],
        issues: list[dict[str, Any]],
        recommendations: list[str],
        jd_id: str | None = None,
    ) -> AnalysisModel:
        """Save analysis metrics and ATS score breakdown."""
        analysis = AnalysisModel(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            jd_id=jd_id,
            overall_score=overall_score,
            grade=grade,
            category_scores=category_scores,
            ats_breakdown=ats_breakdown,
            issues=issues,
            recommendations=recommendations,
        )
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch recent analysis history with resume details."""
        stmt = (
            select(AnalysisModel, ResumeModel)
            .join(ResumeModel, AnalysisModel.resume_id == ResumeModel.id)
            .order_by(AnalysisModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        history = []
        for analysis, resume in result.all():
            history.append({
                "id": analysis.id,
                "resume_id": resume.id,
                "original_filename": resume.original_filename,
                "overall_score": analysis.overall_score,
                "grade": analysis.grade,
                "category_scores": analysis.category_scores,
                "created_at": analysis.created_at.isoformat(),
            })
        return history
