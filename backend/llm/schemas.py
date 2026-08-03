"""LLM schemas — data structures for LLM input/output.

This module defines the structured formats for sending data to LLMs
and validating their responses using Pydantic.
"""

from pydantic import BaseModel, Field


class BulletRewriteRequest(BaseModel):
    """Request to rewrite a bullet point."""

    original: str = Field(..., description="Original bullet text")
    context: str = Field("", description="Job title or context")
    missing_skills: list[str] = Field(default_factory=list, description="Skills to incorporate")


class BulletRewriteResponse(BaseModel):
    """LLM response for bullet rewriting."""

    original: str = Field(..., description="Original bullet text")
    improved: str = Field(..., description="Improved bullet text")
    changes_made: list[str] = Field(default_factory=list, description="What was changed")
    confidence: float = Field(0.8, description="Confidence in improvement (0-1)")


class RewriteRequest(BaseModel):
    """Request to rewrite multiple bullets."""

    bullets: list[BulletRewriteRequest] = Field(..., description="Bullets to rewrite")
    job_title: str = Field("", description="Target job title")
    job_description: str = Field("", description="Job description for context")


class RewriteResponse(BaseModel):
    """Complete rewrite response."""

    rewritten_bullets: list[BulletRewriteResponse] = Field(
        default_factory=list, description="Rewritten bullets"
    )
    total_improved: int = Field(0, description="Number of bullets improved")
    overall_confidence: float = Field(0.0, description="Average confidence")
    validation_passed: bool = Field(True, description="Did validation pass?")


class LLMValidationResult(BaseModel):
    """Result of validating LLM output."""

    is_valid: bool = Field(True, description="Is the output valid?")
    issues: list[str] = Field(default_factory=list, description="Validation issues found")
    original_bullet: str = Field("", description="Original bullet")
    improved_bullet: str = Field("", description="Improved bullet after validation")
