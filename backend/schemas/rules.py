"""Rule engine schemas — data structures for rule evaluation results.

This module defines the output formats for the rule engine,
including individual rule results, issues, and overall scoring.
"""

from pydantic import BaseModel, Field


class Issue(BaseModel):
    """A single issue found by a rule."""

    rule: str = Field(..., description="Rule name that triggered this issue")
    severity: str = Field(..., description="Severity: error, warning, info")
    message: str = Field(..., description="Human-readable issue description")
    section: str = Field("", description="Resume section where issue was found")
    suggestion: str = Field("", description="How to fix this issue")


class RuleOutput(BaseModel):
    """Result from a single rule category."""

    category: str = Field(..., description="Rule category (contact, section, etc.)")
    passed: bool = Field(..., description="Did all rules in this category pass?")
    score: float = Field(0.0, description="Score for this category (0-100)")
    max_score: float = Field(100.0, description="Maximum possible score")
    issues: list[Issue] = Field(default_factory=list, description="Issues found")
    checks_passed: int = Field(0, description="Number of checks passed")
    checks_total: int = Field(0, description="Total number of checks")


class RuleResult(BaseModel):
    """Complete result from the rule engine.

    Contains per-category results and an overall score with all issues.
    """

    filename: str = Field(..., description="Original filename")
    overall_score: float = Field(0.0, description="Overall resume score (0-100)")
    overall_grade: str = Field("", description="Letter grade (A, B, C, D, F)")
    categories: list[RuleOutput] = Field(default_factory=list, description="Category results")
    all_issues: list[Issue] = Field(default_factory=list, description="All issues combined")
    total_checks_passed: int = Field(0, description="Total checks passed")
    total_checks: int = Field(0, description="Total checks run")
    evaluation_time_ms: float = Field(0, description="Time taken (ms)")
