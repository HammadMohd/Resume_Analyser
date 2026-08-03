"""Extraction coordinator — orchestrates all extraction engines.

This module coordinates NER extraction, skills extraction, and date
extraction to produce a complete extraction result from resume text.

Responsibilities:
    - Coordinating all extraction engines
    - Combining results into a unified ExtractionResult
    - Handling extraction failures gracefully

NOT responsible for:
    - Individual extraction logic (belongs to respective extractors)
    - Resume parsing (belongs to parser module)
    - Resume normalization (belongs to structured_parser)
"""

import time

from backend.parser.ner_extractor import NERExtractor
from backend.parser.skills_extractor import SkillsExtractor
from backend.schemas.extraction import (
    ExtractedDate,
    ExtractedEntity,
    ExtractedSkill,
    ExtractionResult,
)
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ExtractionEngine:
    """Coordinate all extraction engines."""

    def __init__(self) -> None:
        """Initialize extraction engines."""
        self.ner = NERExtractor()
        self.skills = SkillsExtractor()

    def extract(self, text: str, filename: str = "") -> ExtractionResult:
        """Extract all entities and skills from resume text.

        Args:
            text: Full resume text.
            filename: Original filename.

        Returns:
            Complete extraction result.
        """
        start = time.time()

        result = ExtractionResult(
            filename=filename,
            extraction_time_ms=0,
            raw_text=text,
        )

        # Extract NER entities
        try:
            ner_entities = self.ner.extract_entities(text)
            result.emails = ner_entities.get("emails", [])
            result.phones = ner_entities.get("phones", [])
            result.urls = ner_entities.get("urls", [])
            result.linkedin = ner_entities.get("linkedin", [])
            result.github = ner_entities.get("github", [])

            # Convert to ExtractedEntity objects
            for email in result.emails:
                result.entities.append(
                    ExtractedEntity(type="email", value=email, confidence=1.0, context="")
                )
            for phone in result.phones:
                result.entities.append(
                    ExtractedEntity(type="phone", value=phone, confidence=1.0, context="")
                )
            for url in result.urls:
                result.entities.append(
                    ExtractedEntity(type="url", value=url, confidence=1.0, context="")
                )
            for linkedin in result.linkedin:
                result.entities.append(
                    ExtractedEntity(
                        type="linkedin", value=linkedin, confidence=1.0, context=""
                    )
                )
            for github in result.github:
                result.entities.append(
                    ExtractedEntity(type="github", value=github, confidence=1.0, context="")
                )

            # Extract dates
            raw_dates = ner_entities.get("dates", [])
            for d in raw_dates:
                result.dates.append(
                    ExtractedDate(
                        start=d.get("start", ""),
                        end=d.get("end", ""),
                        raw=d.get("raw", ""),
                        context="",
                    )
                )
        except Exception as e:
            logger.error("NER extraction failed: %s", str(e))

        # Extract skills
        try:
            raw_skills = self.skills.extract_skills(text)
            for s in raw_skills:
                proficiency = self.skills.detect_proficiency(text, s["skill"])
                result.skills.append(
                    ExtractedSkill(
                        name=s["skill"],
                        category=s["category"],
                        proficiency=proficiency,
                        confidence=s["confidence"],
                        mentions=1,
                    )
                )

            result.skill_categories = self.skills.extract_skills_by_category(text)
        except Exception as e:
            logger.error("Skills extraction failed: %s", str(e))

        elapsed = (time.time() - start) * 1000
        result.extraction_time_ms = round(elapsed, 2)
        logger.info("Extraction completed in %.2f ms", elapsed)

        return result
