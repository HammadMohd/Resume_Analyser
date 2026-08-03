"""Tests for Job Description Engine — Phase 7.

Tests JD skill extraction, experience parsing, and the parse endpoints.
"""

import io

from fastapi.testclient import TestClient

from backend.jd.experience_parser import JDExperienceParser
from backend.jd.jd_parser import JDParser
from backend.jd.skill_extractor import JDSkillExtractor
from backend.main import app
from backend.schemas.jd import JobDescription

# ── JD Skill Extractor Tests ────────────────────────────────────────


class TestJDSkillExtractor:
    """Test JD skill extraction."""

    def setup_method(self):
        self.extractor = JDSkillExtractor()

    def test_extract_required_skills(self):
        text = "Required: Python, Docker, AWS"
        skills = self.extractor.extract_skills(text)
        skill_names = [s.name for s in skills]
        assert "python" in skill_names
        assert "docker" in skill_names
        assert "aws" in skill_names

    def test_extract_preferred_skills(self):
        text = "Nice to have: React, TypeScript"
        skills = self.extractor.extract_skills(text)
        skill_names = [s.name for s in skills]
        assert "react" in skill_names

    def test_distinguish_required_vs_preferred(self):
        text = "Required: Python\nNice to have: React"
        skills = self.extractor.extract_skills(text)
        python_skill = next((s for s in skills if s.name == "python"), None)
        react_skill = next((s for s in skills if s.name == "react"), None)
        assert python_skill is not None
        assert react_skill is not None

    def test_extract_from_job_listing(self):
        text = """We are looking for a Backend Developer.

Required:
- Python, Django, PostgreSQL
- Docker, AWS

Nice to have:
- Kubernetes, Redis"""
        skills = self.extractor.extract_skills(text)
        assert len(skills) >= 4

    def test_empty_text(self):
        skills = self.extractor.extract_skills("")
        assert skills == []


# ── JD Experience Parser Tests ──────────────────────────────────────


class TestJDExperienceParser:
    """Test JD experience parsing."""

    def setup_method(self):
        self.parser = JDExperienceParser()

    def test_parse_years(self):
        text = "3+ years of experience required"
        exp = self.parser.parse(text)
        assert exp.min_years == 3

    def test_parse_year_range(self):
        text = "5-8 years of experience"
        exp = self.parser.parse(text)
        assert exp.min_years == 5
        assert exp.max_years == 8

    def test_parse_senior_level(self):
        text = "Senior developer with 5+ years"
        exp = self.parser.parse(text)
        assert exp.level == "senior"

    def test_parse_entry_level(self):
        text = "Entry level position, 0-2 years"
        exp = self.parser.parse(text)
        assert exp.level == "entry"

    def test_infer_level_from_years(self):
        text = "7 years of experience"
        exp = self.parser.parse(text)
        assert exp.level == "senior"

    def test_empty_text(self):
        exp = self.parser.parse("")
        assert exp.min_years == 0
        assert exp.level == ""


# ── JD Parser Tests ─────────────────────────────────────────────────


class TestJDParser:
    """Test JD parser coordinator."""

    def setup_method(self):
        self.parser = JDParser()

    def test_parse_returns_jd(self):
        text = """Backend Developer at Google

Required: Python, AWS, Docker
3+ years experience
BS in Computer Science"""
        jd = self.parser.parse(text, title="Backend Developer")
        assert isinstance(jd, JobDescription)
        assert jd.title == "Backend Developer"
        assert len(jd.skills) >= 2
        assert jd.experience.min_years == 3

    def test_extract_title_from_text(self):
        text = "Software Engineer\nRequired: Python"
        jd = self.parser.parse(text)
        assert "Software Engineer" in jd.title

    def test_extract_company(self):
        text = "at Google\nRequired: Python"
        jd = self.parser.parse(text)
        assert "Google" in jd.company or jd.company == ""

    def test_extract_keywords(self):
        text = """Backend Developer
Python Django PostgreSQL AWS Docker
Build scalable microservices
REST APIs"""
        jd = self.parser.parse(text)
        assert len(jd.keywords) > 0

    def test_parsing_time_positive(self):
        text = "Python developer required"
        jd = self.parser.parse(text)
        assert jd.parsing_time_ms >= 0

    def test_empty_text(self):
        jd = self.parser.parse("")
        assert isinstance(jd, JobDescription)


# ── Schema Tests ────────────────────────────────────────────────────


class TestJDSchema:
    """Test JD schema validation."""

    def test_minimal_jd(self):
        jd = JobDescription()
        assert jd.title == ""
        assert jd.skills == []

    def test_full_jd(self):
        from backend.schemas.jd import JDExperience, JDSkill

        jd = JobDescription(
            title="Engineer",
            skills=[JDSkill(name="python")],
            experience=JDExperience(min_years=3),
        )
        assert jd.title == "Engineer"
        assert len(jd.skills) == 1


# ── JD Endpoint Tests ───────────────────────────────────────────────


class TestJDEndpoint:
    """Test JD endpoints."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_parse_text_requires_content(self):
        response = self.client.post("/api/v1/jd/parse-text", data={"text": ""})
        assert response.status_code in [400, 422]

    def test_parse_text_returns_200(self):
        response = self.client.post(
            "/api/v1/jd/parse-text",
            data={"text": "Python developer\nRequired: Python, Django"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "skills" in data["data"]

    def test_parse_file_requires_file(self):
        response = self.client.post("/api/v1/jd/parse")
        assert response.status_code == 422

    def test_parse_txt_file(self):
        content = b"Python developer\nRequired: Python, Django, PostgreSQL"
        response = self.client.post(
            "/api/v1/jd/parse",
            files={"file": ("job.txt", io.BytesIO(content), "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
