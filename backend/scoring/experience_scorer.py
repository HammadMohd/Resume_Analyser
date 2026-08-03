"""Experience scorer — calculates experience match score.

Experience is the second most important component (25% weight).
ATS systems check if candidates meet minimum experience requirements.

Scoring logic:
- Years requirement met: 60 points
- Level requirement met: 40 points
- Bonus for exceeding requirements: up to 10 points
"""

from backend.schemas.jd import JobDescription
from backend.schemas.resume import NormalizedResume
from backend.schemas.scoring import ScoreDetail
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def score_experience(resume: NormalizedResume, jd: JobDescription) -> ScoreDetail:
    """Calculate experience match score.

    Args:
        resume: Parsed resume.
        jd: Parsed job description.

    Returns:
        ScoreDetail with experience score and reasoning.
    """
    reasoning = []
    score = 0.0
    max_score = 100.0

    # Calculate resume experience from entries
    resume_years = _estimate_years_experience(resume)
    resume_level = _infer_level(resume_years)

    # JD requirements
    jd_years = jd.experience.min_years
    jd_level = jd.experience.level

    # Score years (60 points)
    if jd_years > 0:
        if resume_years >= jd_years:
            score += 60
            reasoning.append(f"✓ Experience requirement met: {resume_years} years >= {jd_years} required")
            # Bonus for exceeding
            if resume_years > jd_years * 1.5:
                score += 10
                reasoning.append(f"✓ Exceeds requirement by {resume_years - jd_years} years")
        else:
            deficit = jd_years - resume_years
            partial = max(0, 60 - (deficit * 15))
            score += partial
            reasoning.append(f"✗ Experience below requirement: {resume_years} years vs {jd_years} required")
    else:
        score += 30  # Default if no requirement specified
        reasoning.append("No specific years requirement in JD")

    # Score level (40 points)
    if jd_level:
        level_order = {"entry": 1, "mid": 2, "senior": 3, "lead": 4, "executive": 5}
        resume_level_num = level_order.get(resume_level, 1)
        jd_level_num = level_order.get(jd_level, 1)

        if resume_level_num >= jd_level_num:
            score += 40
            reasoning.append(f"✓ Level requirement met: {resume_level} >= {jd_level}")
        else:
            partial = max(0, 40 - ((jd_level_num - resume_level_num) * 20))
            score += partial
            reasoning.append(f"✗ Level below requirement: {resume_level} vs {jd_level} required")
    else:
        score += 20  # Default if no level specified
        reasoning.append("No specific level requirement in JD")

    normalized_score = min(100, score)

    logger.info("Experience score: %.0f/100", normalized_score)

    return ScoreDetail(
        category="experience",
        score=normalized_score,
        max_score=max_score,
        weight=0.25,
        weighted_score=normalized_score * 0.25,
        reasoning=reasoning,
        passed=normalized_score >= 50,
    )


def _estimate_years_experience(resume: NormalizedResume) -> int:
    """Estimate total years from experience entries."""
    # Simple heuristic: count unique companies
    companies = set()
    for exp in resume.experience:
        if exp.company:
            companies.add(exp.company.lower())

    # Rough estimate: assume 2-3 years per company
    return len(companies) * 2 if companies else 0


def _infer_level(years: int) -> str:
    """Infer level from years of experience."""
    if years <= 2:
        return "entry"
    elif years <= 5:
        return "mid"
    elif years <= 8:
        return "senior"
    else:
        return "lead"
