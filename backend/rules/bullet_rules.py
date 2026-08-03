"""Bullet rules — evaluates quality of resume bullet points.

Each bullet point is scored based on:
1. Starts with action verb
2. Contains quantifiable metrics
3. Has appropriate length (not too short/long)
4. Mentions technologies/skills

Scoring per bullet:
- Action verb: 25 points
- Metrics present: 30 points
- Proper length: 25 points
- Technology mentioned: 20 points

Average across all bullets = final bullet score.
"""

import re

from backend.schemas.resume import NormalizedResume
from backend.schemas.rules import Issue, RuleOutput
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Action verbs that should start bullet points
ACTION_VERBS = {
    "achieved", "added", "adepted", "administered", "advanced", "analyzed",
    "architected", "automated", "built", "collaborated", "collected", "consolidated",
    "constructed", "controlled", "coordinated", "created", "decreased", "delivered",
    "demonstrated", "designed", "developed", "directed", "drove", "eliminated",
    "enhanced", "established", "evaluated", "exceeded", "executed", "expanded",
    "facilitated", "fixed", "generated", "grew", "guided", "halved", "handled",
    "implemented", "improved", "increased", "influenced", "initiated", "integrated",
    "introduced", "invented", "launched", "led", "maintained", "managed",
    "marketed", "maximized", "mentored", "migrated", "minimized", "modernized",
    "monitored", "negotiated", "operated", "optimized", "orchestrated", "organized",
    "oversaw", "partnered", "performed", "piloted", "planned", "ported",
    "prioritized", "produced", "programmed", "projected", "proposed", "proved",
    "published", "raised", "rationalized", "reached", "reduced", "refactored",
    "refined", "reinforced", "released", "resolved", "restored", "revamped",
    "saved", "secured", "segmented", "simplified", "solved", "sorted",
    "standardized", "strengthened", "structured", "suggested", "superseded",
    "supported", "surpassed", "targeted", "tested", "trained", "transformed",
    "transitioned", "troubleshoot", "turned", "unified", "updated", "upgraded",
    "utilized", "verified", "visualized", "won", "wrote",
}

# Patterns that indicate metrics
METRIC_PATTERNS = [
    re.compile(r"\d+%"),                          # Percentages
    re.compile(r"\d+\s*(?:million|billion|k|k+)"), # Large numbers
    re.compile(r"\$\d+"),                          # Dollar amounts
    re.compile(r"\d+\s*(?:users|customers|clients|requests|transactions)"),
    re.compile(r"\d+\s*(?:hours|days|weeks|months|years)"),
    re.compile(r"\d+\s*(?:x|times)\s*(?:faster|more|less|improvement)"),
    re.compile(r"by\s*\d+%"),                      # "by 45%"
    re.compile(r"from\s*\d+\s*to\s*\d+"),         # "from 100 to 500"
]


def evaluate_bullets(resume: NormalizedResume) -> RuleOutput:
    """Evaluate quality of all bullet points in resume.

    Args:
        resume: Normalized resume data.

    Returns:
        RuleOutput with score and issues.
    """
    issues: list[Issue] = []
    all_bullets: list[str] = []

    # Collect all bullets from experience
    for exp in resume.experience:
        all_bullets.extend(exp.bullets)

    if not all_bullets:
        issues.append(
            Issue(
                rule="bullets_exist",
                severity="error",
                message="No bullet points found in experience section",
                section="experience",
                suggestion="Add bullet points describing your achievements",
            )
        )
        return RuleOutput(
            category="bullets",
            passed=False,
            score=0,
            max_score=100,
            issues=issues,
            checks_passed=0,
            checks_total=1,
        )

    checks_passed = 0
    checks_total = len(all_bullets) * 4  # 4 checks per bullet
    total_score = 0.0

    for i, bullet in enumerate(all_bullets):
        bullet_score = _score_single_bullet(bullet, i + 1, issues)
        total_score += bullet_score
        checks_passed += sum([
            _has_action_verb(bullet),
            _has_metrics(bullet),
            _has_proper_length(bullet),
            _has_technology(bullet, resume),
        ])

    avg_score = (total_score / len(all_bullets)) if all_bullets else 0

    logger.info("Bullet score: %.0f/100 (%d bullets evaluated)", avg_score, len(all_bullets))

    return RuleOutput(
        category="bullets",
        passed=avg_score >= 70,
        score=avg_score,
        max_score=100,
        issues=issues,
        checks_passed=checks_passed,
        checks_total=checks_total,
    )


def _score_single_bullet(bullet: str, index: int, issues: list[Issue]) -> float:
    """Score a single bullet point (0-100)."""
    score = 0.0

    # Action verb (25 points)
    if _has_action_verb(bullet):
        score += 25
    else:
        issues.append(
            Issue(
                rule="bullet_action_verb",
                severity="warning",
                message=f"Bullet {index} doesn't start with an action verb",
                section="experience",
                suggestion="Start with a strong action verb (e.g., 'Led', 'Built', 'Improved')",
            )
        )

    # Metrics (30 points)
    if _has_metrics(bullet):
        score += 30
    else:
        issues.append(
            Issue(
                rule="bullet_metrics",
                severity="warning",
                message=f"Bullet {index} lacks quantifiable metrics",
                section="experience",
                suggestion="Add numbers, percentages, or measurable outcomes",
            )
        )

    # Proper length (25 points)
    if _has_proper_length(bullet):
        score += 25
    else:
        length = len(bullet)
        if length < 20:
            issues.append(
                Issue(
                    rule="bullet_too_short",
                    severity="warning",
                    message=f"Bullet {index} is too short ({length} chars)",
                    section="experience",
                    suggestion="Expand with more details about your impact",
                )
            )
        else:
            issues.append(
                Issue(
                    rule="bullet_too_long",
                    severity="info",
                    message=f"Bullet {index} is too long ({length} chars)",
                    section="experience",
                    suggestion="Keep bullets concise (1-2 lines ideally)",
                )
            )

    # Technology mention (20 points)
    if _has_technology(bullet, None):
        score += 20

    return score


def _has_action_verb(bullet: str) -> bool:
    """Check if bullet starts with an action verb."""
    first_word = bullet.strip().split()[0].lower() if bullet.strip() else ""
    return first_word in ACTION_VERBS


def _has_metrics(bullet: str) -> bool:
    """Check if bullet contains quantifiable metrics."""
    return any(pattern.search(bullet) for pattern in METRIC_PATTERNS)


def _has_proper_length(bullet: str) -> bool:
    """Check if bullet is proper length (40-200 chars)."""
    length = len(bullet.strip())
    return 40 <= length <= 200


def _has_technology(bullet: str, resume: NormalizedResume | None) -> bool:
    """Check if bullet mentions a technology."""
    tech_keywords = [
        "python", "java", "javascript", "typescript", "react", "angular",
        "node", "django", "flask", "fastapi", "aws", "azure", "docker",
        "kubernetes", "postgresql", "mysql", "mongodb", "redis", "git",
        "api", "rest", "graphql", "sql", "nosql", "ci/cd", "jenkins",
    ]
    bullet_lower = bullet.lower()
    return any(tech in bullet_lower for tech in tech_keywords)
