"""Section detector — identifies resume sections from parsed text.

This module detects and classifies sections in a resume based on
common section headers and patterns.

Responsibilities:
    - Detecting section headers (Experience, Education, Skills, etc.)
    - Classifying sections by type
    - Splitting text into sections
    - Handling various header formats

NOT responsible for:
    - Extracting structured data from sections (belongs to extractor)
    - Parsing individual entries (belongs to structured parser)
"""

import re

from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Section patterns — maps section type to regex patterns
SECTION_PATTERNS: dict[str, list[str]] = {
    "contact": [
        r"^(contact|contact\s+info|contact\s+information)$",
    ],
    "summary": [
        r"^(summary|professional\s+summary|objective|career\s+objective|profile|about\s+me)$",
    ],
    "experience": [
        r"^(experience|work\s+experience|employment|work\s+history|professional\s+experience)$",
    ],
    "education": [
        r"^(education|educational\s+background|academic|qualifications)$",
    ],
    "skills": [
        r"^(skills|technical\s+skills|competencies|technologies|tech\s+stack)$",
    ],
    "projects": [
        r"^(projects|personal\s+projects|key\s+projects|notable\s+projects)$",
    ],
    "certifications": [
        r"^(certifications?|licenses?|credentials?|certificates?)$",
    ],
    "awards": [
        r"^(awards?|honors?|achievements?|recognition)$",
    ],
    "publications": [
        r"^(publications?|papers?|articles?|research)$",
    ],
    "languages": [
        r"^(languages?|foreign\s+languages?)$",
    ],
    "interests": [
        r"^(interests?|hobbies|extracurricular)$",
    ],
}


class SectionDetector:
    """Detect and classify resume sections."""

    def __init__(self) -> None:
        """Initialize with compiled patterns."""
        self._compiled = {}
        for section_type, patterns in SECTION_PATTERNS.items():
            self._compiled[section_type] = [re.compile(p, re.IGNORECASE) for p in patterns]

    def detect_sections(self, text: str) -> list[dict]:
        """Detect sections in resume text.

        Args:
            text: Full resume text.

        Returns:
            List of dicts with 'type', 'title', 'start', 'end' keys.
        """
        lines = text.split("\n")
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            section_type = self._classify_line(stripped)

            if section_type:
                # Close previous section
                if current_section:
                    current_section["end"] = i
                    sections.append(current_section)

                # Start new section
                current_section = {
                    "type": section_type,
                    "title": stripped,
                    "start": i,
                    "end": None,
                }

        # Close last section
        if current_section:
            current_section["end"] = len(lines)
            sections.append(current_section)

        logger.info("Detected %d sections", len(sections))
        return sections

    def _classify_line(self, line: str) -> str | None:
        """Classify a line as a section header.

        Returns section type if matched, None otherwise.
        """
        for section_type, patterns in self._compiled.items():
            for pattern in patterns:
                if pattern.match(line):
                    return section_type
        return None

    def get_section_text(self, text: str, sections: list[dict], section_type: str) -> str:
        """Extract text for a specific section type.

        Args:
            text: Full resume text.
            sections: Detected sections list.
            section_type: Type of section to extract.

        Returns:
            Text content of the section.
        """
        lines = text.split("\n")
        for section in sections:
            if section["type"] == section_type:
                start = section["start"] + 1  # Skip header line
                end = section["end"]
                return "\n".join(lines[start:end]).strip()
        return ""
