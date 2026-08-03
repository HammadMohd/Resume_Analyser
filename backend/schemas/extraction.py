"""Extraction schemas — data structures for extracted entities.

This module defines the schemas for all extracted data from resumes,
including entities, skills, and the complete extraction result.
"""

from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    """A single extracted entity."""

    type: str = Field(..., description="Entity type (email, phone, etc.)")
    value: str = Field(..., description="Entity value")
    confidence: float = Field(1.0, description="Extraction confidence (0-1)")
    context: str = Field("", description="Surrounding text context")


class ExtractedSkill(BaseModel):
    """An extracted skill with metadata."""

    name: str = Field(..., description="Skill name")
    category: str = Field("", description="Skill category")
    proficiency: str = Field("not_specified", description="Detected proficiency")
    confidence: float = Field(1.0, description="Extraction confidence (0-1)")
    mentions: int = Field(1, description="Number of mentions")


class ExtractedDate(BaseModel):
    """An extracted date or date range."""

    start: str = Field("", description="Start date")
    end: str = Field("", description="End date or 'Present'")
    raw: str = Field("", description="Original date text")
    context: str = Field("", description="Associated text (job title, etc.)")


class ExtractionResult(BaseModel):
    """Complete result from the extraction engine.

    Contains all extracted entities, skills, and metadata from a resume.
    """

    filename: str = Field(..., description="Original filename")
    entities: list[ExtractedEntity] = Field(default_factory=list, description="Extracted entities")
    skills: list[ExtractedSkill] = Field(default_factory=list, description="Extracted skills")
    dates: list[ExtractedDate] = Field(default_factory=list, description="Extracted dates")
    emails: list[str] = Field(default_factory=list, description="Email addresses")
    phones: list[str] = Field(default_factory=list, description="Phone numbers")
    urls: list[str] = Field(default_factory=list, description="URLs found")
    linkedin: list[str] = Field(default_factory=list, description="LinkedIn profiles")
    github: list[str] = Field(default_factory=list, description="GitHub profiles")
    skill_categories: dict[str, list[str]] = Field(
        default_factory=dict, description="Skills grouped by category"
    )
    extraction_time_ms: float = Field(0, description="Time taken (ms)")
    raw_text: str = Field("", description="Original text")
