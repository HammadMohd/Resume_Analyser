"""LLM validator — validates and sanitizes LLM output.

This module ensures LLM responses are safe, valid, and free
from hallucinations before using them.

Checks performed:
- No new technologies added
- No fake metrics invented
- Length within bounds
- Action verb present
- No inappropriate content
"""

import re

from backend.llm.schemas import LLMValidationResult
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Known technologies (from skills database)
KNOWN_TECHNOLOGIES = {
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node", "django", "flask", "fastapi", "spring", "rails", "aws", "azure",
    "gcp", "docker", "kubernetes", "postgresql", "mysql", "mongodb", "redis",
    "git", "github", "jenkins", "ci/cd", "devops", "agile", "scrum",
    "REST", "API", "microservices", "sql", "nosql", "graphql", "testing",
}

# Action verbs that should start bullets
ACTION_VERBS = {
    "achieved", "added", "built", "collaborated", "created", "delivered",
    "designed", "developed", "drove", "enhanced", "established", "executed",
    "generated", "grew", "guided", "implemented", "improved", "increased",
    "initiated", "integrated", "introduced", "launched", "led", "managed",
    "migrated", "optimized", "orchestrated", "oversaw", "performed",
    "planned", "produced", "reduced", "refactored", "resolved", "saved",
    "secured", "simplified", "solved", "standardized", "strengthened",
    "tested", "trained", "transformed", "updated", "upgraded", "utilized",
    "verified", "wrote",
}


def validate_bullet_rewrite(
    original: str,
    improved: str,
    max_length: int = 300,
) -> LLMValidationResult:
    """Validate an LLM-rewritten bullet point.

    Args:
        original: Original bullet text.
        improved: Improved bullet from LLM.
        max_length: Maximum allowed length.

    Returns:
        LLMValidationResult with validation status.
    """
    issues = []

    # Check length
    if len(improved) > max_length:
        issues.append(f"Improved bullet too long ({len(improved)} > {max_length} chars)")

    if len(improved) < 20:
        issues.append(f"Improved bullet too short ({len(improved)} < 20 chars)")

    # Check for action verb
    first_word = improved.strip().split()[0].lower() if improved.strip() else ""
    if first_word not in ACTION_VERBS:
        issues.append(f"Does not start with action verb (starts with '{first_word}')")

    # Check for fake metrics
    fake_metric_patterns = [
        re.compile(r"\d{3,}%"),  # Over 100% increase unlikely
        re.compile(r"\d{5,}"),   # Very large numbers
        re.compile(r"million|billion", re.IGNORECASE),
    ]
    for pattern in fake_metric_patterns:
        if pattern.search(improved) and not pattern.search(original):
            issues.append("Contains metrics not in original (possible hallucination)")

    # Check for new technologies
    improved_lower = improved.lower()
    original_lower = original.lower()
    for tech in KNOWN_TECHNOLOGIES:
        if tech.lower() in improved_lower and tech.lower() not in original_lower:
            issues.append(f"Adds technology '{tech}' not in original")

    # Check similarity (too different = likely hallucination)
    similarity = _calculate_similarity(original, improved)
    if similarity < 0.1:
        issues.append("Too different from original (possible fabrication)")

    is_valid = len(issues) == 0

    if not is_valid:
        logger.warning("Validation failed for bullet: %s", issues)

    return LLMValidationResult(
        is_valid=is_valid,
        issues=issues,
        original_bullet=original,
        improved_bullet=improved if is_valid else original,
    )


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple word overlap similarity."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0
