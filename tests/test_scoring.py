"""Tests for ATS Scoring Engine — Phase 9.

Tests skills scoring, experience scoring, ATS scorer, and endpoints.
"""

from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.jd import JDExperience, JDSkill, JobDescription
from backend.schemas.resume import (
    ContactInfo,
    Education,
    Experience,
    NormalizedResume,
    Project,
    SkillCategory,
)
from backend.schemas.scoring import ATSScore, ScoreDetail
from backend.scoring.ats_scorer import ATSScorer
from backend.scoring.experience_scorer import score_experience
from backend.scoring.skills_scorer import score_skills

# ── Skills Scorer Tests ─────────────────────────────────────────────


class TestSkillsScorer:
    """Test skills match scoring."""

    def test_all_required_skills_matched(self):
        resume = NormalizedResume(
            filename="test.pdf",
            skills=[SkillCategory(category="Langs", skills=["Python", "Docker", "AWS"])],
        )
        jd = JobDescription(
            skills=[
                JDSkill(name="Python", required=True),
                JDSkill(name="Docker", required=True),
                JDSkill(name="AWS", required=True),
            ]
        )
        result = score_skills(resume, jd)
        assert result.score == 100
        assert result.passed is True

    def test_partial_skills_matched(self):
        resume = NormalizedResume(
            filename="test.pdf", skills=[SkillCategory(category="Langs", skills=["Python"])]
        )
        jd = JobDescription(
            skills=[
                JDSkill(name="Python", required=True),
                JDSkill(name="AWS", required=True),
            ]
        )
        result = score_skills(resume, jd)
        assert 0 < result.score < 100

    def test_no_skills_matched(self):
        resume = NormalizedResume(
            filename="test.pdf", skills=[SkillCategory(category="Langs", skills=["Java"])]
        )
        jd = JobDescription(
            skills=[
                JDSkill(name="Python", required=True),
                JDSkill(name="AWS", required=True),
            ]
        )
        result = score_skills(resume, jd)
        assert result.score == 0
        assert result.passed is False

    def test_preferred_skills_bonus(self):
        resume = NormalizedResume(
            filename="test.pdf",
            skills=[SkillCategory(category="Langs", skills=["Python", "Redis"])],
        )
        jd = JobDescription(
            skills=[
                JDSkill(name="Python", required=True),
                JDSkill(name="Redis", required=False),
            ]
        )
        result = score_skills(resume, jd)
        assert result.score == 100

    def test_no_jd_skills(self):
        resume = NormalizedResume(
            filename="test.pdf", skills=[SkillCategory(category="Langs", skills=["Python"])]
        )
        jd = JobDescription(skills=[])
        result = score_skills(resume, jd)
        assert result.passed is False


# ── Experience Scorer Tests ─────────────────────────────────────────


class TestExperienceScorer:
    """Test experience match scoring."""

    def test_experience_meets_requirement(self):
        resume = NormalizedResume(
            filename="test.pdf",
            experience=[
                Experience(company="Google", title="Engineer"),
                Experience(company="Meta", title="Engineer"),
                Experience(company="Amazon", title="Engineer"),
            ],
        )
        jd = JobDescription(experience=JDExperience(min_years=3, level="mid"))
        result = score_experience(resume, jd)
        assert result.score >= 60

    def test_experience_below_requirement(self):
        resume = NormalizedResume(
            filename="test.pdf",
            experience=[
                Experience(company="Startup", title="Junior"),
            ],
        )
        jd = JobDescription(experience=JDExperience(min_years=5, level="senior"))
        result = score_experience(resume, jd)
        assert result.score < 80

    def test_no_experience_requirement(self):
        resume = NormalizedResume(
            filename="test.pdf", experience=[Experience(company="Google", title="Engineer")]
        )
        jd = JobDescription(experience=JDExperience())
        result = score_experience(resume, jd)
        assert result.score >= 50


# ── ATS Scorer Tests ────────────────────────────────────────────────


class TestATSScorer:
    """Test ATS scorer coordinator."""

    def setup_method(self):
        self.scorer = ATSScorer()

    def test_perfect_match(self):
        resume = NormalizedResume(
            filename="resume.pdf",
            contact=ContactInfo(email="test@test.com", phone="555-123-4567"),
            summary="Senior engineer",
            experience=[
                Experience(company="Google", title="Senior Engineer", bullets=["Led team"]),
                Experience(company="Meta", title="Engineer", bullets=["Built systems"]),
            ],
            skills=[SkillCategory(category="Langs", skills=["Python", "Docker", "AWS"])],
            education=[Education(institution="MIT", degree="BS CS")],
            projects=[Project(name="Project 1", description="Built something")],
        )
        jd = JobDescription(
            title="Senior Developer",
            skills=[
                JDSkill(name="Python", required=True),
                JDSkill(name="Docker", required=True),
            ],
            experience=JDExperience(min_years=3, level="senior"),
        )
        result = self.scorer.score(resume, jd)
        assert isinstance(result, ATSScore)
        assert result.overall_score >= 60
        assert result.overall_grade in ["A", "B", "C"]

    def test_poor_match(self):
        resume = NormalizedResume(filename="resume.pdf")
        jd = JobDescription(
            title="Senior Developer",
            skills=[
                JDSkill(name="Python", required=True),
                JDSkill(name="Docker", required=True),
            ],
            experience=JDExperience(min_years=5, level="senior"),
        )
        result = self.scorer.score(resume, jd)
        assert result.overall_score < 40
        assert result.overall_grade in ["D", "F"]

    def test_score_has_breakdown(self):
        resume = NormalizedResume(filename="resume.pdf")
        jd = JobDescription(title="Developer")
        result = self.scorer.score(resume, jd)
        assert result.breakdown.skills is not None
        assert result.breakdown.experience is not None

    def test_recommendations_generated(self):
        resume = NormalizedResume(filename="resume.pdf")
        jd = JobDescription(skills=[JDSkill(name="Python", required=True)])
        result = self.scorer.score(resume, jd)
        assert len(result.recommendations) > 0

    def test_missing_skills_identified(self):
        resume = NormalizedResume(
            filename="test.pdf", skills=[SkillCategory(category="Langs", skills=["Java"])]
        )
        jd = JobDescription(skills=[JDSkill(name="Python", required=True)])
        result = self.scorer.score(resume, jd)
        assert "Python" in result.missing_skills

    def test_scoring_time_positive(self):
        resume = NormalizedResume(filename="resume.pdf")
        jd = JobDescription(title="Developer")
        result = self.scorer.score(resume, jd)
        assert result.scoring_time_ms >= 0


# ── Schema Tests ────────────────────────────────────────────────────


class TestScoringSchema:
    """Test scoring schemas."""

    def test_score_detail_minimal(self):
        detail = ScoreDetail(category="test", score=80)
        assert detail.category == "test"
        assert detail.score == 80

    def test_ats_score_minimal(self):
        from backend.schemas.scoring import ScoreBreakdown

        breakdown = ScoreBreakdown(
            skills=ScoreDetail(category="skills", score=80),
            experience=ScoreDetail(category="experience", score=70),
            projects=ScoreDetail(category="projects", score=60),
            education=ScoreDetail(category="education", score=90),
            structure=ScoreDetail(category="structure", score=85),
            formatting=ScoreDetail(category="formatting", score=75),
        )
        score = ATSScore(
            resume_filename="test.pdf",
            breakdown=breakdown,
        )
        assert score.resume_filename == "test.pdf"


# ── Scoring Endpoint Tests ──────────────────────────────────────────


class TestScoringEndpoint:
    """Test scoring endpoints."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_analyze_text_requires_both(self):
        response = self.client.post(
            "/api/v1/score/analyze-text",
            data={"resume_text": "", "jd_text": ""},
        )
        assert response.status_code in [400, 422]

    def test_analyze_text_returns_200(self):
        response = self.client.post(
            "/api/v1/score/analyze-text",
            data={
                "resume_text": "Python developer with Docker experience",
                "jd_text": "Looking for Python developer with Docker skills",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "overall_score" in data["data"]
        assert "breakdown" in data["data"]

    def test_analyze_requires_files(self):
        response = self.client.post("/api/v1/score/analyze")
        assert response.status_code == 422
