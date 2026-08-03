"""Resume schemas — normalized resume data structures.

This module defines the standardized JSON schema for resumes.
All parsed resumes are normalized into this format regardless
of the original document structure.

Responsibilities:
    - Defining resume section structures
    - Enforcing consistent field names
    - Providing validation for normalized data
"""

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact information extracted from resume."""

    name: str = Field("", description="Full name")
    email: str = Field("", description="Email address")
    phone: str = Field("", description="Phone number")
    linkedin: str = Field("", description="LinkedIn URL")
    github: str = Field("", description="GitHub URL")
    location: str = Field("", description="City/State/Country")
    website: str = Field("", description="Personal website")


class Education(BaseModel):
    """Education entry."""

    institution: str = Field("", description="School/university name")
    degree: str = Field("", description="Degree obtained")
    field_of_study: str = Field("", description="Major/field")
    start_date: str = Field("", description="Start date (YYYY-MM or YYYY)")
    end_date: str = Field("", description="End date or 'Present'")
    gpa: str = Field("", description="GPA if mentioned")
    description: str = Field("", description="Additional details")


class Experience(BaseModel):
    """Work experience entry."""

    company: str = Field("", description="Company name")
    title: str = Field("", description="Job title")
    location: str = Field("", description="Job location")
    start_date: str = Field("", description="Start date")
    end_date: str = Field("", description="End date or 'Present'")
    bullets: list[str] = Field(default_factory=list, description="Job responsibilities")
    description: str = Field("", description="Full description text")


class Project(BaseModel):
    """Project entry."""

    name: str = Field("", description="Project name")
    description: str = Field("", description="Project description")
    technologies: list[str] = Field(default_factory=list, description="Tech stack")
    url: str = Field("", description="Project URL")
    bullets: list[str] = Field(default_factory=list, description="Key features")


class SkillCategory(BaseModel):
    """Skills grouped by category."""

    category: str = Field("", description="Skill category name")
    skills: list[str] = Field(default_factory=list, description="Skills in category")


class Certification(BaseModel):
    """Certification entry."""

    name: str = Field("", description="Certification name")
    issuer: str = Field("", description="Issuing organization")
    date: str = Field("", description="Date obtained")
    url: str = Field("", description="Credential URL")


class ResumeSection(BaseModel):
    """A detected section in the resume."""

    section_type: str = Field(..., description="Section type (contact, experience, etc.)")
    title: str = Field("", description="Original section title")
    content: str = Field("", description="Raw section text")
    confidence: float = Field(1.0, description="Detection confidence (0-1)")


class NormalizedResume(BaseModel):
    """Fully normalized resume in standard JSON format.

    This is the canonical representation of a resume after parsing
    and normalization. All downstream processing uses this format.
    """

    filename: str = Field(..., description="Original filename")
    contact: ContactInfo = Field(
        default_factory=lambda: ContactInfo(), description="Contact information"
    )
    summary: str = Field("", description="Professional summary/objective")
    experience: list[Experience] = Field(default_factory=list, description="Work experience")
    education: list[Education] = Field(default_factory=list, description="Education history")
    skills: list[SkillCategory] = Field(default_factory=list, description="Skills by category")
    projects: list[Project] = Field(default_factory=list, description="Projects")
    certifications: list[Certification] = Field(default_factory=list, description="Certifications")
    sections_detected: list[ResumeSection] = Field(
        default_factory=list, description="Detected sections"
    )
    raw_text: str = Field("", description="Original parsed text")
    normalization_time_ms: float = Field(0, description="Time taken (ms)")
