"""Hybrid search — combines BM25 and embedding search.

This module orchestrates keyword-based (BM25) and semantic (embedding)
search to produce a comprehensive match score between resume and JD.

Why hybrid?
- BM25 catches exact matches (skills, technologies)
- Embeddings catch synonyms and related concepts
- Combined score is more accurate than either alone

Weighting:
- BM25: 0.6 (keywords matter more for ATS)
- Embeddings: 0.4 (semantics provide nuance)
"""

import time

from backend.search.bm25_search import BM25Search
from backend.search.embedding_search import EmbeddingSearch
from backend.schemas.jd import JobDescription
from backend.schemas.resume import NormalizedResume
from backend.schemas.search import MatchResult, SkillMatch, BM25Result, EmbeddingResult
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Weights for combining scores
BM25_WEIGHT = 0.6
EMBEDDING_WEIGHT = 0.4


class HybridSearch:
    """Hybrid search combining BM25 and embeddings."""

    def __init__(self) -> None:
        """Initialize search engines."""
        self.bm25 = BM25Search()
        self.embeddings = EmbeddingSearch()

    def match(self, resume: NormalizedResume, jd: JobDescription) -> MatchResult:
        """Match a resume against a job description.

        Args:
            resume: Parsed and normalized resume.
            jd: Parsed job description.

        Returns:
            MatchResult with scores and skill matches.
        """
        start = time.time()

        # Prepare texts for search
        resume_text = self._prepare_resume_text(resume)
        jd_text = self._prepare_jd_text(jd)

        # BM25 search
        bm25_result = self.bm25.score(jd_text, resume_text)

        # Embedding search
        embedding_result = self.embeddings.score(resume_text, jd_text)

        # Combine scores
        bm25_score = bm25_result.score * 100
        embedding_score = embedding_result.score * 100
        overall_score = (bm25_result.score * BM25_WEIGHT + embedding_result.score * EMBEDDING_WEIGHT) * 100

        # Skill-by-skill matching
        resume_skills = self._extract_all_skills(resume)
        jd_skills = [s.name for s in jd.skills]
        skill_matches = self._match_skills(resume_skills, jd_skills)

        matching_skills = [m.skill for m in skill_matches if m.match_type != "missing"]
        missing_skills = [m.skill for m in skill_matches if m.match_type == "missing"]
        extra_skills = [s for s in resume_skills if s not in jd_skills]

        elapsed = (time.time() - start) * 1000

        logger.info(
            "Match completed: %.1f%% overall (BM25: %.1f%%, Embedding: %.1f%%)",
            overall_score, bm25_score, embedding_score,
        )

        return MatchResult(
            resume_filename=resume.filename,
            jd_title=jd.title,
            overall_score=overall_score,
            bm25_score=bm25_score,
            embedding_score=embedding_score,
            bm25_result=bm25_result,
            embedding_result=embedding_result,
            skill_matches=skill_matches,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            extra_skills=extra_skills,
            match_time_ms=round(elapsed, 2),
        )

    def _prepare_resume_text(self, resume: NormalizedResume) -> str:
        """Prepare resume text for search."""
        parts = []

        # Add contact
        if resume.contact.name:
            parts.append(resume.contact.name)

        # Add summary
        if resume.summary:
            parts.append(resume.summary)

        # Add experience bullets
        for exp in resume.experience:
            if exp.title:
                parts.append(exp.title)
            if exp.company:
                parts.append(exp.company)
            parts.extend(exp.bullets)

        # Add skills
        for cat in resume.skills:
            parts.extend(cat.skills)

        # Add education
        for edu in resume.education:
            if edu.degree:
                parts.append(edu.degree)
            if edu.institution:
                parts.append(edu.institution)

        return " ".join(parts)

    def _prepare_jd_text(self, jd: JobDescription) -> str:
        """Prepare JD text for search."""
        parts = []

        if jd.title:
            parts.append(jd.title)
        if jd.description:
            parts.append(jd.description)
        for skill in jd.skills:
            parts.append(skill.name)

        return " ".join(parts)

    def _extract_all_skills(self, resume: NormalizedResume) -> list[str]:
        """Extract all skills from resume."""
        skills = []
        for cat in resume.skills:
            skills.extend(cat.skills)
        return skills

    def _match_skills(self, resume_skills: list[str], jd_skills: list[str]) -> list[SkillMatch]:
        """Match resume skills against JD skills."""
        matches = []
        resume_set = set(s.lower() for s in resume_skills)

        for jd_skill in jd_skills:
            jd_lower = jd_skill.lower()
            if jd_lower in resume_set:
                matches.append(SkillMatch(
                    skill=jd_skill,
                    in_resume=True,
                    in_jd=True,
                    match_type="exact",
                ))
            else:
                # Check for partial match
                partial = any(jd_lower in s.lower() or s.lower() in jd_lower for s in resume_skills)
                matches.append(SkillMatch(
                    skill=jd_skill,
                    in_resume=partial,
                    in_jd=True,
                    match_type="partial" if partial else "missing",
                ))

        return matches
