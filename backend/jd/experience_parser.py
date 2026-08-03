"""JD experience parser — extracts experience requirements from job descriptions.

This module parses experience requirements like "3+ years of Python"
and extracts years, level, and related context.

Responsibilities:
    - Extracting years of experience required
    - Detecting experience level (junior, mid, senior)
    - Parsing experience-related context

NOT responsible for:
    - Resume experience parsing (belongs to structured_parser)
    - Skill extraction (belongs to skill_extractor)
"""

import re

from backend.schemas.jd import JDExperience
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Years patterns
YEARS_PATTERNS = [
    # "3-5 years" (check range first before single)
    re.compile(r"(\d+)\s*[-–—]\s*(\d+)\s*(?:years?|yrs?)", re.IGNORECASE),
    # "3+ years" or "3+ years of experience"
    re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience)?", re.IGNORECASE),
    # "at least 3 years"
    re.compile(r"at\s+least\s+(\d+)\s*(?:years?|yrs?)", re.IGNORECASE),
    # "minimum 3 years"
    re.compile(r"minimum\s+(\d+)\s*(?:years?|yrs?)", re.IGNORECASE),
]

# Level patterns
LEVEL_PATTERNS = [
    (re.compile(r"\b(?:entry[\s-]level|junior|associate|intern)\b", re.IGNORECASE), "entry"),
    (re.compile(r"\b(?:mid[\s-]level|intermediate)\b", re.IGNORECASE), "mid"),
    (re.compile(r"\b(?:senior|sr\.?|experienced)\b", re.IGNORECASE), "senior"),
    (re.compile(r"\b(?:lead|principal|staff|architect)\b", re.IGNORECASE), "lead"),
    (re.compile(r"\b(?:director|vp|vice[\s-]president|c[\s-]?to|head)\b", re.IGNORECASE), "executive"),
]


class JDExperienceParser:
    """Parse experience requirements from job descriptions."""

    def parse(self, text: str) -> JDExperience:
        """Parse experience requirements from JD text.

        Args:
            text: Job description text.

        Returns:
            JDExperience with parsed requirements.
        """
        min_years = 0
        max_years = 0
        level = ""
        raw_text = ""

        # Extract years
        for pattern in YEARS_PATTERNS:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                min_years = int(groups[0])
                if len(groups) > 1 and groups[1]:
                    max_years = int(groups[1])
                raw_text = match.group(0)
                break

        # Detect level
        for pattern, lvl in LEVEL_PATTERNS:
            if pattern.search(text):
                level = lvl
                if not raw_text:
                    raw_text = match.group(0) if match else ""
                break

        # Infer level from years if not explicitly stated
        if not level and min_years > 0:
            level = self._infer_level_from_years(min_years)

        experience = JDExperience(
            min_years=min_years,
            max_years=max_years,
            level=level,
            raw_text=raw_text,
        )

        logger.info("Parsed experience: %d+ years, level=%s", min_years, level)
        return experience

    def _infer_level_from_years(self, years: int) -> str:
        """Infer experience level from years."""
        if years <= 2:
            return "entry"
        elif years <= 5:
            return "mid"
        elif years <= 8:
            return "senior"
        else:
            return "lead"
