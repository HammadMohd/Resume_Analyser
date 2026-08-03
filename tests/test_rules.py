"""Tests for rule engine — Phase 6.

Tests contact rules, section rules, bullet rules, and the validate endpoint.
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.rules.bullet_rules import evaluate_bullets
from backend.rules.contact_rules import evaluate_contact
from backend.rules.rule_engine import RuleEngine
from backend.rules.section_rules import evaluate_sections
from backend.schemas.resume import (
    ContactInfo,
    Education,
    Experience,
    NormalizedResume,
    SkillCategory,
)
from backend.schemas.rules import RuleResult

# ── Contact Rules Tests ─────────────────────────────────────────────


class TestContactRules:
    """Test contact information validation."""

    def test_all_contact_present(self):
        contact = ContactInfo(
            name="John",
            email="john@test.com",
            phone="555-123-4567",
            linkedin="linkedin.com/in/john",
            github="github.com/john",
        )
        result = evaluate_contact(contact)
        assert result.score == 100
        assert result.passed is True
        assert len(result.issues) == 0

    def test_missing_email(self):
        contact = ContactInfo(phone="555-123-4567")
        result = evaluate_contact(contact)
        assert result.score < 100
        assert any(i.rule == "contact_email" for i in result.issues)

    def test_missing_phone(self):
        contact = ContactInfo(email="john@test.com")
        result = evaluate_contact(contact)
        assert result.score < 100
        assert any(i.rule == "contact_phone" for i in result.issues)

    def test_missing_linkedin(self):
        contact = ContactInfo(email="john@test.com", phone="555-123-4567")
        result = evaluate_contact(contact)
        assert result.score < 100
        assert any(i.rule == "contact_linkedin" for i in result.issues)

    def test_empty_contact(self):
        contact = ContactInfo()
        result = evaluate_contact(contact)
        assert result.score == 0
        assert len(result.issues) == 4


# ── Section Rules Tests ─────────────────────────────────────────────


class TestSectionRules:
    """Test resume section validation."""

    def test_all_sections_present(self):
        resume = NormalizedResume(
            filename="test.pdf",
            summary="Experienced developer",
            experience=[Experience(company="Google", title="Engineer")],
            skills=[SkillCategory(category="Langs", skills=["Python"])],
            education=[Education(institution="MIT", degree="BS CS")],
        )
        result = evaluate_sections(resume)
        assert result.score == 100
        assert result.passed is True

    def test_missing_experience(self):
        resume = NormalizedResume(
            filename="test.pdf",
            skills=[SkillCategory(category="Langs", skills=["Python"])],
            education=[Education(institution="MIT", degree="BS CS")],
        )
        result = evaluate_sections(resume)
        assert result.score < 100
        assert any(i.rule == "section_experience" for i in result.issues)

    def test_missing_skills(self):
        resume = NormalizedResume(
            filename="test.pdf",
            experience=[Experience(company="Google", title="Engineer")],
            education=[Education(institution="MIT", degree="BS CS")],
        )
        result = evaluate_sections(resume)
        assert result.score < 100
        assert any(i.rule == "section_skills" for i in result.issues)

    def test_missing_education(self):
        resume = NormalizedResume(
            filename="test.pdf",
            experience=[Experience(company="Google", title="Engineer")],
            skills=[SkillCategory(category="Langs", skills=["Python"])],
        )
        result = evaluate_sections(resume)
        assert result.score < 100
        assert any(i.rule == "section_education" for i in result.issues)

    def test_empty_resume(self):
        resume = NormalizedResume(filename="test.pdf")
        result = evaluate_sections(resume)
        assert result.score == 0


# ── Bullet Rules Tests ──────────────────────────────────────────────


class TestBulletRules:
    """Test bullet point quality evaluation."""

    def test_good_bullets(self):
        resume = NormalizedResume(
            filename="test.pdf",
            experience=[
                Experience(
                    company="Google",
                    title="Engineer",
                    bullets=[
                        "Led team of 5 engineers to deliver microservices architecture",
                        "Improved API response time by 45% through caching optimization",
                    ],
                )
            ],
        )
        result = evaluate_bullets(resume)
        assert result.score > 50

    def test_no_bullets(self):
        resume = NormalizedResume(
            filename="test.pdf",
            experience=[Experience(company="Google", title="Engineer")],
        )
        result = evaluate_bullets(resume)
        assert result.score == 0
        assert any(i.rule == "bullets_exist" for i in result.issues)

    def test_short_bullets(self):
        resume = NormalizedResume(
            filename="test.pdf",
            experience=[
                Experience(
                    company="Google",
                    title="Engineer",
                    bullets=["Did stuff"],
                )
            ],
        )
        result = evaluate_bullets(resume)
        assert any(i.rule == "bullet_too_short" for i in result.issues)

    def test_bullet_without_metrics(self):
        resume = NormalizedResume(
            filename="test.pdf",
            experience=[
                Experience(
                    company="Google",
                    title="Engineer",
                    bullets=[
                        "Developed and maintained various backend services for the team"
                    ],
                )
            ],
        )
        result = evaluate_bullets(resume)
        assert any(i.rule == "bullet_metrics" for i in result.issues)


# ── Rule Engine Tests ───────────────────────────────────────────────


class TestRuleEngine:
    """Test rule engine coordinator."""

    def setup_method(self):
        self.engine = RuleEngine()

    def test_evaluate_returns_result(self):
        resume = NormalizedResume(
            filename="test.pdf",
            contact=ContactInfo(
                name="John",
                email="john@test.com",
                phone="555-123-4567",
            ),
            summary="Developer",
            experience=[
                Experience(
                    company="Google",
                    title="Engineer",
                    bullets=["Led team and improved performance by 30%"],
                )
            ],
            skills=[SkillCategory(category="Langs", skills=["Python"])],
            education=[Education(institution="MIT", degree="BS CS")],
        )
        result = self.engine.evaluate(resume)
        assert isinstance(result, RuleResult)
        assert result.filename == "test.pdf"
        assert 0 <= result.overall_score <= 100
        assert result.overall_grade in ["A", "B", "C", "D", "F"]

    def test_perfect_resume(self):
        resume = NormalizedResume(
            filename="test.pdf",
            contact=ContactInfo(
                name="John Doe",
                email="john@test.com",
                phone="555-123-4567",
                linkedin="linkedin.com/in/john",
                github="github.com/john",
            ),
            summary="Senior engineer with 10 years experience",
            experience=[
                Experience(
                    company="Google",
                    title="Senior Engineer",
                    bullets=[
                        "Led team of 5 engineers to deliver microservices architecture",
                        "Improved API response time by 45% through caching optimization",
                    ],
                )
            ],
            skills=[SkillCategory(category="Langs", skills=["Python", "Go"])],
            education=[Education(institution="MIT", degree="BS CS")],
        )
        result = self.engine.evaluate(resume)
        assert result.overall_score >= 70
        assert result.overall_grade in ["A", "B", "C"]

    def test_empty_resume(self):
        resume = NormalizedResume(filename="test.pdf")
        result = self.engine.evaluate(resume)
        assert result.overall_score < 50
        assert result.overall_grade in ["D", "F"]


# ── Schema Tests ────────────────────────────────────────────────────


class TestRuleSchema:
    """Test rule output schemas."""

    def test_rule_result_minimal(self):
        result = RuleResult(filename="test.pdf")
        assert result.filename == "test.pdf"
        assert result.overall_score == 0


# ── Validate Endpoint Tests ─────────────────────────────────────────


class TestValidateEndpoint:
    """Test POST /api/v1/resumes/validate endpoint."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_validate_requires_file(self):
        response = self.client.post("/api/v1/resumes/validate")
        assert response.status_code == 422

    @patch("backend.api.routes.resume.RuleEngine")
    @patch("backend.api.routes.resume.StructuredParser")
    @patch("backend.api.routes.resume.ResumeParser")
    @patch("backend.api.routes.resume.UploadService")
    def test_validate_returns_200(
        self, MockUpload, MockParser, MockStructured, MockEngine
    ):
        # Mock upload
        mock_upload = MagicMock()
        mock_upload.upload_resume = AsyncMock(return_value={
            "data": {
                "stored_filename": "abc123.pdf",
                "original_filename": "resume.pdf",
                "upload_timestamp": MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
            }
        })
        MockUpload.return_value = mock_upload

        # Mock parser
        mock_parser = MagicMock()
        mock_parser.parse.return_value = MagicMock(raw_text="Python developer")
        MockParser.return_value = mock_parser

        # Mock structured parser
        mock_structured = MagicMock()
        mock_structured.parse_resume.return_value = NormalizedResume(
            filename="resume.pdf"
        )
        MockStructured.return_value = mock_structured

        # Mock rule engine
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = RuleResult(
            filename="resume.pdf",
            overall_score=85,
            overall_grade="B",
        )
        MockEngine.return_value = mock_engine

        file_content = io.BytesIO(b"fake pdf content")
        response = self.client.post(
            "/api/v1/resumes/validate",
            files={"file": ("resume.pdf", file_content, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "validation" in data["data"]
        assert data["data"]["validation"]["overall_score"] == 85
