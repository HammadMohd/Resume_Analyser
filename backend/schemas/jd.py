"""Job Description schemas — data structures for parsed job descriptions.

This module defines the standardized format for job descriptions
after parsing, including skills, experience, and education requirements.
"""

from pydantic import BaseModel, Field


class JDSkill(BaseModel):
    """A skill extracted from a job description."""

    name: str = Field(..., description="Skill name")
    required: bool = Field(True, description="Is this skill required or preferred?")
    category: str = Field("", description="Skill category")
    confidence: float = Field(1.0, description="Extraction confidence (0-1)")


class JDExperience(BaseModel):
    """Experience requirements from a job description."""

    min_years: int = Field(0, description="Minimum years required")
    max_years: int = Field(0, description="Maximum years (0 = no max)")
    level: str = Field("", description="Level: entry, mid, senior, lead, executive")
    raw_text: str = Field("", description="Original experience text")


class JDEducation(BaseModel):
    """Education requirements from a job description."""

    degree: str = Field("", description="Required degree (BS, MS, PhD, etc.)")
    field: str = Field("", description="Field of study")
    required: bool = Field(True, description="Is this required or preferred?")
    raw_text: str = Field("", description="Original education text")


class JobDescription(BaseModel):
    """Fully parsed job description in structured format.

    This is the canonical representation of a job description
    after parsing. Used for comparison with resumes.
    """

    title: str = Field("", description="Job title")
    company: str = Field("", description="Company name")
    location: str = Field("", description="Job location")
    description: str = Field("", description="Full job description text")
    skills: list[JDSkill] = Field(default_factory=list, description="Required/preferred skills")
    experience: JDExperience = Field(default_factory=JDExperience, description="Experience requirements")
    education: list[JDEducation] = Field(default_factory=list, description="Education requirements")
    keywords: list[str] = Field(default_factory=list, description="Important keywords")
    raw_text: str = Field("", description="Original text")
    parsing_time_ms: float = Field(0, description="Time taken (ms)")


class JDUploadResponse(BaseModel):
    """Response schema for JD upload."""

    success: bool = Field(True, description="Upload success")
    message: str = Field("", description="Status message")
    data: JobDescription = Field(..., description="Parsed job description")
