"""Tests for Hybrid Search Engine — Phase 8.

Tests BM25 search, embedding search, hybrid matching, and endpoints.
"""

from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.jd import JDSkill, JobDescription
from backend.schemas.resume import (
    Experience,
    NormalizedResume,
    SkillCategory,
)
from backend.schemas.search import MatchResult
from backend.search.bm25_search import BM25Search
from backend.search.embedding_search import EmbeddingSearch
from backend.search.hybrid_search import HybridSearch

# ── BM25 Search Tests ───────────────────────────────────────────────


class TestBM25Search:
    """Test BM25 keyword search."""

    def setup_method(self):
        self.bm25 = BM25Search()

    def test_identical_texts_high_score(self):
        query = "Python developer with Docker experience"
        doc = "Python developer with Docker experience"
        result = self.bm25.score(query, doc)
        assert result.score > 0.5

    def test_related_texts_moderate_score(self):
        query = "Python developer"
        doc = "Experienced Python programmer and software engineer"
        result = self.bm25.score(query, doc)
        assert result.score > 0

    def test_unrelated_texts_low_score(self):
        query = "Python developer"
        doc = "Marketing manager with social media experience"
        result = self.bm25.score(query, doc)
        assert result.score < 0.5

    def test_matched_terms_identified(self):
        query = "Python Docker AWS"
        doc = "Experience with Python and Docker on AWS"
        result = self.bm25.score(query, doc)
        assert len(result.matched_terms) >= 2

    def test_empty_query(self):
        result = self.bm25.score("", "Some document")
        assert result.score == 0.0

    def test_empty_document(self):
        result = self.bm25.score("query", "")
        assert result.score == 0.0

    def test_skill_matching(self):
        resume_skills = ["Python", "Docker", "AWS"]
        jd_skills = ["Python", "AWS", "Kubernetes"]
        score = self.bm25.score_skills(resume_skills, jd_skills)
        assert 0 < score <= 1


# ── Embedding Search Tests ──────────────────────────────────────────


class TestEmbeddingSearch:
    """Test embedding similarity search."""

    def setup_method(self):
        self.search = EmbeddingSearch()

    def test_identical_texts_high_similarity(self):
        text = "Python developer with Docker experience"
        result = self.search.score(text, text)
        assert result.score > 0.9

    def test_related_texts_moderate_similarity(self):
        text1 = "Python developer"
        text2 = "Experienced Python programmer"
        result = self.search.score(text1, text2)
        assert result.score > 0.5

    def test_different_lengths(self):
        text1 = "Python"
        text2 = "Python developer with extensive experience in building scalable applications"
        result = self.search.score(text1, text2)
        assert 0 <= result.score <= 1

    def test_encode_returns_vector(self):
        vec = self.search.encode("test text")
        assert isinstance(vec, list)
        assert len(vec) > 0

    def test_cosine_similarity_identical(self):
        vec = [1.0, 2.0, 3.0]
        sim = self.search.cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        sim = self.search.cosine_similarity(vec1, vec2)
        assert abs(sim) < 0.001

    def test_empty_text(self):
        result = self.search.score("", "")
        assert 0 <= result.score <= 1


# ── Hybrid Search Tests ─────────────────────────────────────────────


class TestHybridSearch:
    """Test hybrid search coordinator."""

    def setup_method(self):
        self.search = HybridSearch()

    def test_match_returns_result(self):
        resume = NormalizedResume(
            filename="resume.pdf",
            skills=[SkillCategory(category="Langs", skills=["Python", "Docker"])],
            experience=[Experience(company="Google", title="Engineer")],
        )
        jd = JobDescription(
            title="Backend Developer",
            skills=[JDSkill(name="Python"), JDSkill(name="AWS")],
        )
        result = self.search.match(resume, jd)
        assert isinstance(result, MatchResult)
        assert 0 <= result.overall_score <= 100

    def test_perfect_match(self):
        resume = NormalizedResume(
            filename="resume.pdf",
            skills=[SkillCategory(category="Langs", skills=["Python", "Docker", "AWS"])],
        )
        jd = JobDescription(
            title="Developer",
            skills=[JDSkill(name="Python"), JDSkill(name="Docker"), JDSkill(name="AWS")],
        )
        result = self.search.match(resume, jd)
        assert len(result.matching_skills) == 3
        assert len(result.missing_skills) == 0

    def test_partial_match(self):
        resume = NormalizedResume(
            filename="resume.pdf",
            skills=[SkillCategory(category="Langs", skills=["Python"])],
        )
        jd = JobDescription(
            title="Developer",
            skills=[JDSkill(name="Python"), JDSkill(name="AWS"), JDSkill(name="Docker")],
        )
        result = self.search.match(resume, jd)
        assert len(result.matching_skills) >= 1
        assert len(result.missing_skills) >= 1

    def test_no_match(self):
        resume = NormalizedResume(
            filename="resume.pdf",
            skills=[SkillCategory(category="Langs", skills=["Python"])],
        )
        jd = JobDescription(
            title="Marketing Manager",
            skills=[JDSkill(name="SEO"), JDSkill(name="Social Media")],
        )
        result = self.search.match(resume, jd)
        assert len(result.matching_skills) == 0

    def test_match_time_positive(self):
        resume = NormalizedResume(filename="resume.pdf")
        jd = JobDescription(title="Developer")
        result = self.search.match(resume, jd)
        assert result.match_time_ms >= 0


# ── Schema Tests ────────────────────────────────────────────────────


class TestSearchSchema:
    """Test search schemas."""

    def test_match_result_minimal(self):
        result = MatchResult()
        assert result.overall_score == 0

    def test_match_result_full(self):
        result = MatchResult(
            resume_filename="resume.pdf",
            jd_title="Developer",
            overall_score=85.5,
            matching_skills=["Python"],
            missing_skills=["AWS"],
        )
        assert result.overall_score == 85.5
        assert "Python" in result.matching_skills


# ── Search Endpoint Tests ───────────────────────────────────────────


class TestSearchEndpoint:
    """Test search endpoints."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_match_text_requires_both(self):
        response = self.client.post(
            "/api/v1/search/match-text",
            data={"resume_text": "", "jd_text": ""},
        )
        assert response.status_code in [400, 422]

    def test_match_text_returns_200(self):
        response = self.client.post(
            "/api/v1/search/match-text",
            data={
                "resume_text": "Python developer with Docker experience",
                "jd_text": "Looking for Python developer with Docker skills",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "overall_score" in data["data"]

    def test_match_requires_files(self):
        response = self.client.post("/api/v1/search/match")
        assert response.status_code == 422
