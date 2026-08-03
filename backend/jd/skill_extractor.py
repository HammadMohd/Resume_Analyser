"""JD skill extractor — extracts skills from job descriptions.

This module identifies required and preferred skills mentioned
in job descriptions by matching against known skill patterns.

Responsibilities:
    - Extracting skills from JD text
    - Distinguishing required vs preferred skills
    - Categorizing skills

NOT responsible for:
    - Resume skill extraction (belongs to skills_extractor)
    - Experience parsing (belongs to experience_parser)
"""

import re

from backend.parser.skills_extractor import SKILL_DATABASE, ALL_SKILLS
from backend.schemas.jd import JDSkill
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Patterns that indicate required vs preferred
REQUIRED_PATTERNS = [
    re.compile(r"required[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"must\s+(?:have|know|understand)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"essential[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"minimum\s+(?:qualifications?|requirements?)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
]

PREFERRED_PATTERNS = [
    re.compile(r"preferred[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"nice\s+to\s+have[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"bonus[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"plus[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"desired[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
]


class JDSkillExtractor:
    """Extract skills from job descriptions."""

    def __init__(self) -> None:
        """Initialize with compiled patterns."""
        self._skill_patterns: dict[str, re.Pattern] = {}
        for skill in ALL_SKILLS:
            escaped = re.escape(skill)
            self._skill_patterns[skill] = re.compile(
                r"\b" + escaped + r"\b", re.IGNORECASE
            )

    def extract_skills(self, text: str) -> list[JDSkill]:
        """Extract all skills from JD text.

        Args:
            text: Job description text.

        Returns:
            List of JDSkill with required/preferred status.
        """
        skills = []
        seen = set()

        # First, try to extract skills from structured sections
        required_section = self._extract_section(text, REQUIRED_PATTERNS)
        preferred_section = self._extract_section(text, PREFERRED_PATTERNS)

        # Match skills in required section
        if required_section:
            for skill in self._find_skills_in_text(required_section):
                if skill.name not in seen:
                    seen.add(skill.name)
                    skill.required = True
                    skills.append(skill)

        # Match skills in preferred section
        if preferred_section:
            for skill in self._find_skills_in_text(preferred_section):
                if skill.name not in seen:
                    seen.add(skill.name)
                    skill.required = False
                    skills.append(skill)

        # If no structured sections, scan entire text
        if not skills:
            for skill in self._find_skills_in_text(text):
                if skill.name not in seen:
                    seen.add(skill.name)
                    skills.append(skill)

        logger.info("Extracted %d skills from JD", len(skills))
        return skills

    def _extract_section(self, text: str, patterns: list[re.Pattern]) -> str:
        """Extract text following specific patterns."""
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def _find_skills_in_text(self, text: str) -> list[JDSkill]:
        """Find known skills in text."""
        found = []
        text_lower = text.lower()

        for skill in ALL_SKILLS:
            if skill in text_lower:
                pattern = self._skill_patterns[skill]
                matches = pattern.findall(text)
                if matches:
                    category = self._get_category(skill)
                    found.append(
                        JDSkill(
                            name=skill,
                            category=category,
                            confidence=min(1.0, len(matches) * 0.3 + 0.5),
                        )
                    )

        return found

    def _get_category(self, skill: str) -> str:
        """Get the category for a skill."""
        for category, skills in SKILL_DATABASE.items():
            if skill in [s.lower() for s in skills]:
                return category
        return "other"
