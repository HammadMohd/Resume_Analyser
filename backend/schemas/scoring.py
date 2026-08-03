"""Scoring schemas — data structures for ATS scoring results.

This module defines the output formats for the ATS scoring engine,
including score breakdowns and explanations.
"""

from pydantic import BaseModel, Field


class ScoreDetail(BaseModel):
    """Detailed score for a single category."""

    category: str = Field(..., description="Score category name")
    score: float = Field(0.0, description="Score achieved (0-100)")
    max_score: float = Field(100.0, description="Maximum possible score")
    weight: float = Field(0.0, description="Weight in final score (0-1)")
    weighted_score: float = Field(0.0, description="Score × weight")
    reasoning: list[str] = Field(default_factory=list, description="Explanation of score")
    passed: bool = Field(True, description="Did this category pass?")


class ScoreBreakdown(BaseModel):
    """Complete breakdown of all scoring components."""

    skills: ScoreDetail = Field(..., description="Skills match score")
    experience: ScoreDetail = Field(..., description="Experience match score")
    projects: ScoreDetail = Field(..., description="Projects relevance score")
    education: ScoreDetail = Field(..., description="Education match score")
    structure: ScoreDetail = Field(..., description="Resume structure score")
    formatting: ScoreDetail = Field(..., description="Formatting quality score")


class ATSScore(BaseModel):
    """Complete ATS scoring result.

    Contains the overall score, breakdown by category,
    and detailed explanations for each deduction.
    """

    resume_filename: str = Field("", description="Resume filename")
    jd_title: str = Field("", description="Job description title")
    overall_score: float = Field(0.0, description="Overall ATS score (0-100)")
    overall_grade: str = Field("", description="Letter grade (A-F)")
    breakdown: ScoreBreakdown = Field(..., description="Score breakdown by category")
    total_deductions: float = Field(0.0, description="Total points deducted")
    missing_skills: list[str] = Field(default_factory=list, description="Skills not found")
    recommendations: list[str] = Field(default_factory=list, description="Improvement suggestions")
    scoring_time_ms: float = Field(0, description="Time taken (ms)")
