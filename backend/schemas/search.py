"""Search schemas — data structures for search/matching results.

This module defines the output formats for the hybrid search engine,
including BM25 scores, embedding similarity, and combined results.
"""

from pydantic import BaseModel, Field


class BM25Result(BaseModel):
    """Result from BM25 keyword search."""

    score: float = Field(0.0, description="BM25 score (0-1)")
    matched_terms: list[str] = Field(default_factory=list, description="Terms that matched")
    term_scores: dict[str, float] = Field(default_factory=dict, description="Score per term")


class EmbeddingResult(BaseModel):
    """Result from embedding similarity search."""

    score: float = Field(0.0, description="Cosine similarity score (0-1)")
    resume_embedding_dim: int = Field(0, description="Embedding dimension")
    jd_embedding_dim: int = Field(0, description="JD embedding dimension")


class SkillMatch(BaseModel):
    """A single skill match between resume and JD."""

    skill: str = Field(..., description="Skill name")
    in_resume: bool = Field(False, description="Is this in the resume?")
    in_jd: bool = Field(False, description="Is this in the JD?")
    match_type: str = Field("", description="exact, partial, or semantic")


class MatchResult(BaseModel):
    """Complete result from hybrid search matching.

    Contains individual scores from BM25 and embeddings,
    combined score, and detailed match information.
    """

    resume_filename: str = Field("", description="Resume filename")
    jd_title: str = Field("", description="Job description title")
    overall_score: float = Field(0.0, description="Combined match score (0-100)")
    bm25_score: float = Field(0.0, description="BM25 component score (0-100)")
    embedding_score: float = Field(0.0, description="Embedding component score (0-100)")
    bm25_result: BM25Result = Field(default_factory=BM25Result, description="Detailed BM25 result")
    embedding_result: EmbeddingResult = Field(
        default_factory=EmbeddingResult, description="Detailed embedding result"
    )
    skill_matches: list[SkillMatch] = Field(
        default_factory=list, description="Skill-by-skill matches"
    )
    matching_skills: list[str] = Field(default_factory=list, description="Skills found in both")
    missing_skills: list[str] = Field(
        default_factory=list, description="Skills in JD but not resume"
    )
    extra_skills: list[str] = Field(default_factory=list, description="Skills in resume but not JD")
    match_time_ms: float = Field(0, description="Time taken (ms)")
