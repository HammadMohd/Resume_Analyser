"""Skills scorer — calculates skills match score.

Skills are the most important component (35% weight) because
ATS systems primarily filter by keyword matching.

Scoring logic:
- Required skills matched: 10 points each
- Preferred skills matched: 5 points each
- Partial matches: 3 points each
"""

from backend.schemas.jd import JobDescription
from backend.schemas.resume import NormalizedResume
from backend.schemas.scoring import ScoreDetail
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def score_skills(resume: NormalizedResume, jd: JobDescription) -> ScoreDetail:
    """Calculate skills match score.

    Args:
        resume: Parsed resume.
        jd: Parsed job description.

    Returns:
        ScoreDetail with skills score and reasoning.
    """
    reasoning = []
    score = 0.0
    max_score = 100.0

    # Extract resume skills
    resume_skills = set()
    for cat in resume.skills:
        for skill in cat.skills:
            resume_skills.add(skill.lower())

    # Extract JD skills with required/preferred status
    jd_skills = {s.name.lower(): s.required for s in jd.skills}

    if not jd_skills:
        reasoning.append("No skills specified in job description")
        return ScoreDetail(
            category="skills",
            score=0,
            max_score=max_score,
            weight=0.35,
            weighted_score=0,
            reasoning=reasoning,
            passed=False,
        )

    # Score required skills (10 points each)
    required_skills = [s for s, req in jd_skills.items() if req]
    preferred_skills = [s for s, req in jd_skills.items() if not req]

    required_matched = 0
    for skill in required_skills:
        if skill in resume_skills:
            score += 10
            required_matched += 1
            reasoning.append(f"✓ Required skill '{skill}' matched")
        else:
            reasoning.append(f"✗ Required skill '{skill}' missing")

    # Score preferred skills (5 points each)
    preferred_matched = 0
    for skill in preferred_skills:
        if skill in resume_skills:
            score += 5
            preferred_matched += 1
            reasoning.append(f"✓ Preferred skill '{skill}' matched")
        else:
            reasoning.append(f"✗ Preferred skill '{skill}' not found")

    # Normalize to 0-100
    max_possible = len(required_skills) * 10 + len(preferred_skills) * 5
    if max_possible > 0:
        normalized_score = (score / max_possible) * 100
    else:
        normalized_score = 0

    # Summary
    total_matched = required_matched + preferred_matched
    total_skills = len(required_skills) + len(preferred_skills)
    reasoning.insert(0, f"Matched {total_matched}/{total_skills} skills")

    logger.info("Skills score: %.0f/100 (%d/%d matched)", normalized_score, total_matched, total_skills)

    return ScoreDetail(
        category="skills",
        score=normalized_score,
        max_score=max_score,
        weight=0.35,
        weighted_score=normalized_score * 0.35,
        reasoning=reasoning,
        passed=normalized_score >= 50,
    )
