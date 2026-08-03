"""Completeness rules — overall resume completeness evaluation.

Combines all rule results into a final score and provides
comprehensive feedback on resume quality.

Grading scale:
- A (90-100): Excellent, ATS-ready
- B (80-89): Good, minor improvements needed
- C (70-69): Average, several improvements needed
- D (60-69): Below average, significant improvements needed
- F (<60): Poor, major rewrite recommended
"""

from backend.schemas.resume import NormalizedResume
from backend.schemas.rules import Issue, RuleOutput
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def evaluate_completeness(
    resume: NormalizedResume,
    category_results: list[RuleOutput],
) -> RuleOutput:
    """Evaluate overall resume completeness.

    Args:
        resume: Normalized resume data.
        category_results: Results from other rule categories.

    Returns:
        RuleOutput with overall score and issues.
    """
    issues: list[Issue] = []

    # Weight categories for overall score
    weights = {
        "contact": 0.25,
        "sections": 0.35,
        "bullets": 0.40,
    }

    weighted_score = 0.0
    total_weight = 0.0

    for result in category_results:
        weight = weights.get(result.category, 0)
        if weight > 0:
            weighted_score += result.score * weight
            total_weight += weight

    overall_score = weighted_score / total_weight if total_weight > 0 else 0

    # Check experience count
    if len(resume.experience) == 0:
        issues.append(
            Issue(
                rule="completeness_no_experience",
                severity="error",
                message="No work experience entries found",
                section="experience",
                suggestion="Add at least one work experience entry",
            )
        )
    elif len(resume.experience) == 1:
        issues.append(
            Issue(
                rule="completeness_one_experience",
                severity="warning",
                message="Only one work experience entry found",
                section="experience",
                suggestion="Add more experience entries if you have them",
            )
        )

    # Check skills count
    total_skills = sum(len(cat.skills) for cat in resume.skills)
    if total_skills == 0:
        issues.append(
            Issue(
                rule="completeness_no_skills",
                severity="error",
                message="No skills listed",
                section="skills",
                suggestion="Add relevant technical and soft skills",
            )
        )
    elif total_skills < 5:
        issues.append(
            Issue(
                rule="completeness_few_skills",
                severity="warning",
                message=f"Only {total_skills} skills listed",
                section="skills",
                suggestion="Add more relevant skills (aim for 10-15)",
            )
        )

    # Check education count
    if len(resume.education) == 0:
        issues.append(
            Issue(
                rule="completeness_no_education",
                severity="warning",
                message="No education entries found",
                section="education",
                suggestion="Add your educational background",
            )
        )

    # Check summary presence
    if not resume.summary:
        issues.append(
            Issue(
                rule="completeness_no_summary",
                severity="info",
                message="No professional summary found",
                section="summary",
                suggestion="Add a 2-3 sentence professional summary",
            )
        )

    # Determine grade
    grade = _calculate_grade(overall_score)

    logger.info("Overall completeness: %.0f/100 (Grade: %s)", overall_score, grade)

    return RuleOutput(
        category="completeness",
        passed=overall_score >= 70,
        score=overall_score,
        max_score=100,
        issues=issues,
        checks_passed=sum(1 for i in issues if i.severity == "info"),
        checks_total=len(issues),
    )


def _calculate_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
