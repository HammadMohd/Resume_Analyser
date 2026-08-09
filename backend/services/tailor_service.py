"""Resume Tailoring Service — orchestrates intelligent resume tailoring against job descriptions."""

from typing import Any

from pydantic import BaseModel

from backend.llm.star_rewriter import STARBulletEnhancer
from backend.schemas.jd import JobDescription
from backend.schemas.resume import NormalizedResume
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class BulletTailorResult(BaseModel):
    original: str
    tailored: str
    target_skill: str | None
    explanation: str


class ResumeTailorResponse(BaseModel):
    target_job_title: str
    missing_skills_targeted: list[str]
    tailored_bullets: list[BulletTailorResult]
    predicted_score_boost: float
    summary: str


class ResumeTailorService:
    """Service for auto-tailoring candidate resume experience to target job requirements."""

    def __init__(self) -> None:
        self.enhancer = STARBulletEnhancer()

    def tailor_resume(
        self,
        resume: NormalizedResume,
        jd: JobDescription,
    ) -> ResumeTailorResponse:
        """Tailor experience bullets to incorporate missing target skills from JD."""
        resume_skills_lower = {s.lower() for cat in resume.skills for s in cat.skills}
        missing_skills = [s.name for s in jd.skills if s.name.lower() not in resume_skills_lower]

        tailored_results: list[BulletTailorResult] = []

        all_bullets = []
        for exp in resume.experience:
            for b in exp.bullets:
                all_bullets.append((exp.title, b))

        for i, (role, bullet) in enumerate(all_bullets[:5]):
            target_skill = missing_skills[i % len(missing_skills)] if missing_skills else None
            enhanced = self.enhancer.enhance_bullet(
                original_bullet=bullet,
                target_skill=target_skill,
                job_context=f"{role} - {jd.title}",
            )

            tailored_results.append(
                BulletTailorResult(
                    original=bullet,
                    tailored=enhanced.star_bullet,
                    target_skill=target_skill,
                    explanation=f"Rebuilt with STAR framework and integrated missing JD skill '{target_skill}'" if target_skill else "Rebuilt with STAR framework and metrics",
                )
            )

        predicted_boost = min(25.0, len(missing_skills) * 4.5 + 8.0)

        return ResumeTailorResponse(
            target_job_title=jd.title or "Target Position",
            missing_skills_targeted=missing_skills[:5],
            tailored_bullets=tailored_results,
            predicted_score_boost=round(predicted_boost, 1),
            summary=f"Successfully tailored experience bullets to incorporate {len(missing_skills[:5])} missing target skills.",
        )
