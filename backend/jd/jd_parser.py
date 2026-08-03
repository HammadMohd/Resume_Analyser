"""JD parser — coordinates job description parsing.

This module orchestrates skill extraction, experience parsing,
and keyword extraction to produce a structured job description.

Responsibilities:
    - Coordinating all JD parsing components
    - Combining results into JobDescription
    - Extracting title, company, location

NOT responsible for:
    - Individual extraction logic (belongs to respective parsers)
    - Resume comparison (belongs to search/scoring modules)
"""

import re
import time

from backend.jd.experience_parser import JDExperienceParser
from backend.jd.skill_extractor import JDSkillExtractor
from backend.schemas.jd import JDEducation, JobDescription
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Title patterns (usually first line or after common prefixes)
TITLE_PATTERNS = [
    re.compile(r"^(?:job\s+title[:\s]*)?(.+?)(?:\n|$)", re.IGNORECASE),
]

# Company patterns
COMPANY_PATTERNS = [
    re.compile(r"(?:company|organization|employer)[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"at\s+([A-Z][a-zA-Z\s&]+?)(?:\s*[-–—|]|$)", re.MULTILINE),
]

# Location patterns
LOCATION_PATTERNS = [
    re.compile(r"(?:location|office|based\s+in)[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(?:Remote|Hybrid|On[\s-]site)", re.IGNORECASE),
]

# Education patterns
EDUCATION_PATTERNS = [
    re.compile(r"(?:BS|BA|Bachelor(?:'s)?)[\s]+(?:in|of)\s+([^\n,]+)", re.IGNORECASE),
    re.compile(r"(?:MS|MA|Master(?:'s)?)[\s]+(?:in|of)\s+([^\n,]+)", re.IGNORECASE),
    re.compile(r"(?:PhD|Doctorate)[\s]+(?:in|of)\s+([^\n,]+)", re.IGNORECASE),
    re.compile(r"(?:degree|education)[:\s]*([^\n]+)", re.IGNORECASE),
]


class JDParser:
    """Parse job descriptions into structured format."""

    def __init__(self) -> None:
        """Initialize sub-parsers."""
        self.skill_extractor = JDSkillExtractor()
        self.experience_parser = JDExperienceParser()

    def parse(self, text: str, title: str = "", company: str = "") -> JobDescription:
        """Parse a job description.

        Args:
            text: Full JD text.
            title: Optional job title override.
            company: Optional company name override.

        Returns:
            Parsed JobDescription.
        """
        start = time.time()

        # Extract title
        if not title:
            title = self._extract_title(text)

        # Extract company
        if not company:
            company = self._extract_company(text)

        # Extract location
        location = self._extract_location(text)

        # Extract skills
        skills = self.skill_extractor.extract_skills(text)

        # Extract experience
        experience = self.experience_parser.parse(text)

        # Extract education
        education = self._extract_education(text)

        # Extract keywords
        keywords = self._extract_keywords(text)

        elapsed = (time.time() - start) * 1000

        jd = JobDescription(
            title=title,
            company=company,
            location=location,
            description=text,
            skills=skills,
            experience=experience,
            education=education,
            keywords=keywords,
            raw_text=text,
            parsing_time_ms=round(elapsed, 2),
        )

        logger.info(
            "JD parsed in %.2f ms: %d skills, %d years required",
            elapsed,
            len(skills),
            experience.min_years,
        )
        return jd

    def _extract_title(self, text: str) -> str:
        """Extract job title from text."""
        for pattern in TITLE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        # Default to first line
        first_line = text.split("\n")[0].strip()
        return first_line[:100] if first_line else ""

    def _extract_company(self, text: str) -> str:
        """Extract company name from text."""
        for pattern in COMPANY_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_location(self, text: str) -> str:
        """Extract location from text."""
        for pattern in LOCATION_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0).strip()
        return ""

    def _extract_education(self, text: str) -> list[JDEducation]:
        """Extract education requirements."""
        education = []
        seen = set()

        for pattern in EDUCATION_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                field = match.strip()
                if field and field not in seen:
                    seen.add(field)
                    education.append(
                        JDEducation(
                            degree=self._infer_degree(field),
                            field=field,
                            required=True,
                        )
                    )

        return education

    def _infer_degree(self, text: str) -> str:
        """Infer degree level from text."""
        text_lower = text.lower()
        if "phd" in text_lower or "doctorate" in text_lower:
            return "PhD"
        elif "master" in text_lower or "ms" in text_lower or "ma" in text_lower:
            return "MS"
        elif "bachelor" in text_lower or "bs" in text_lower or "ba" in text_lower:
            return "BS"
        return "BS"  # Default

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction based on frequency and importance
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
        word_freq: dict[str, int] = {}

        # Common stop words to ignore
        stop_words = {
            "this",
            "that",
            "with",
            "from",
            "have",
            "will",
            "been",
            "were",
            "they",
            "their",
            "would",
            "could",
            "should",
            "about",
            "more",
            "also",
            "into",
            "only",
            "than",
            "them",
            "some",
            "such",
            "very",
            "when",
            "what",
            "which",
            "who",
            "how",
            "all",
            "each",
            "both",
            "few",
            "most",
            "other",
        }

        for word in words:
            word_lower = word.lower()
            if word_lower not in stop_words:
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        # Return top keywords by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:20]]
