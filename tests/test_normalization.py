"""Tests for resume normalization — Phase 4.

Tests section detection, structured parsing, and the normalize endpoint.
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.parser.section_detector import SectionDetector
from backend.parser.structured_parser import StructuredParser
from backend.schemas.resume import (
    ContactInfo,
    Education,
    Experience,
    NormalizedResume,
    SkillCategory,
)


# ── Section Detector Tests ──────────────────────────────────────────


class TestSectionDetector:
    """Test section detection from resume text."""

    def setup_method(self):
        self.detector = SectionDetector()

    def test_detect_experience_section(self):
        text = "Experience\nSoftware Engineer at Google\n- Built systems"
        sections = self.detector.detect_sections(text)
        assert len(sections) == 1
        assert sections[0]["type"] == "experience"

    def test_detect_education_section(self):
        text = "Education\nBS Computer Science, MIT 2018-2022"
        sections = self.detector.detect_sections(text)
        assert len(sections) == 1
        assert sections[0]["type"] == "education"

    def test_detect_skills_section(self):
        text = "Skills\nPython, JavaScript, React"
        sections = self.detector.detect_sections(text)
        assert len(sections) == 1
        assert sections[0]["type"] == "skills"

    def test_detect_multiple_sections(self):
        text = "Experience\nEngineer at Google\n\nEducation\nBS CS MIT"
        sections = self.detector.detect_sections(text)
        assert len(sections) == 2
        types = [s["type"] for s in sections]
        assert "experience" in types
        assert "education" in types

    def test_detect_summary_section(self):
        text = "Summary\nSenior engineer with 10 years experience"
        sections = self.detector.detect_sections(text)
        assert len(sections) == 1
        assert sections[0]["type"] == "summary"

    def test_no_sections_detected(self):
        text = "Just some random text without headers"
        sections = self.detector.detect_sections(text)
        assert len(sections) == 0

    def test_get_section_text(self):
        text = "Experience\nEngineer at Google\n- Built systems\n\nEducation\nBS MIT"
        sections = self.detector.detect_sections(text)
        exp_text = self.detector.get_section_text(text, sections, "experience")
        assert "Engineer at Google" in exp_text

    def test_case_insensitive_headers(self):
        text = "EXPERIENCE\nEngineer at Google"
        sections = self.detector.detect_sections(text)
        assert len(sections) == 1
        assert sections[0]["type"] == "experience"


# ── Structured Parser Tests ─────────────────────────────────────────


class TestStructuredParser:
    """Test structured parsing of resume sections."""

    def setup_method(self):
        self.parser = StructuredParser()

    def test_parse_contact_info(self):
        text = """Contact
John Doe
john@example.com
555-123-4567
linkedin.com/in/johndoe"""
        resume = self.parser.parse_resume(text, "test.pdf")
        assert resume.contact.name == "John Doe"
        assert resume.contact.email == "john@example.com"
        assert resume.contact.phone == "555-123-4567"
        assert "linkedin.com/in/johndoe" in resume.contact.linkedin

    def test_parse_experience(self):
        text = """Experience
Senior Engineer at Google, Jan 2020 - Present
- Led team of 5
- Built microservices

Engineer at Meta, Jun 2018 - Dec 2019
- Developed features"""
        resume = self.parser.parse_resume(text, "test.pdf")
        assert len(resume.experience) >= 1
        assert resume.experience[0].company == "Google"
        assert len(resume.experience[0].bullets) >= 1

    def test_parse_education(self):
        text = """Education
BS Computer Science from MIT, 2018 - 2022
GPA: 3.8"""
        resume = self.parser.parse_resume(text, "test.pdf")
        assert len(resume.education) >= 1
        assert resume.education[0].institution == "MIT"

    def test_parse_skills(self):
        text = """Skills
Programming: Python, JavaScript, Go
Frameworks: React, FastAPI, Django"""
        resume = self.parser.parse_resume(text, "test.pdf")
        assert len(resume.skills) >= 1
        all_skills = []
        for cat in resume.skills:
            all_skills.extend(cat.skills)
        assert "Python" in all_skills

    def test_parse_projects(self):
        text = """Projects
Resume Analyzer
- Built with FastAPI
- PDF parsing support"""
        resume = self.parser.parse_resume(text, "test.pdf")
        assert len(resume.projects) >= 1
        assert resume.projects[0].name == "Resume Analyzer"

    def test_empty_text(self):
        resume = self.parser.parse_resume("", "test.pdf")
        assert resume.contact.name == ""
        assert len(resume.experience) == 0

    def test_raw_text_preserved(self):
        text = "Experience\nEngineer at Google"
        resume = self.parser.parse_resume(text, "test.pdf")
        assert resume.raw_text == text

    def test_filename_preserved(self):
        text = "Experience\nEngineer at Google"
        resume = self.parser.parse_resume(text, "my_resume.pdf")
        assert resume.filename == "my_resume.pdf"

    def test_normalization_time_positive(self):
        text = "Experience\nEngineer at Google"
        resume = self.parser.parse_resume(text, "test.pdf")
        assert resume.normalization_time_ms >= 0


# ── Schema Tests ────────────────────────────────────────────────────


class TestResumeSchema:
    """Test resume schema validation."""

    def test_minimal_resume(self):
        resume = NormalizedResume(filename="test.pdf")
        assert resume.filename == "test.pdf"
        assert resume.contact.name == ""
        assert resume.experience == []

    def test_full_resume(self):
        resume = NormalizedResume(
            filename="test.pdf",
            contact=ContactInfo(name="John", email="john@test.com"),
            experience=[
                Experience(company="Google", title="Engineer", bullets=["Built stuff"])
            ],
            education=[
                Education(institution="MIT", degree="BS CS")
            ],
            skills=[SkillCategory(category="Langs", skills=["Python"])],
        )
        assert resume.contact.name == "John"
        assert len(resume.experience) == 1
        assert resume.experience[0].company == "Google"


# ── Normalize Endpoint Tests ────────────────────────────────────────


class TestNormalizeEndpoint:
    """Test POST /api/v1/resumes/normalize endpoint."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_normalize_requires_file(self):
        response = self.client.post("/api/v1/resumes/normalize")
        assert response.status_code == 422

    @patch("backend.api.routes.resume.StructuredParser")
    @patch("backend.api.routes.resume.ResumeParser")
    @patch("backend.api.routes.resume.UploadService")
    def test_normalize_returns_200(self, MockUpload, MockParser, MockStructured):
        # Mock upload (async method)
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
        mock_parser.parse.return_value = MagicMock(raw_text="Experience\nEngineer")
        MockParser.return_value = mock_parser

        # Mock structured parser
        mock_structured = MagicMock()
        mock_structured.parse_resume.return_value = NormalizedResume(
            filename="resume.pdf"
        )
        MockStructured.return_value = mock_structured

        file_content = io.BytesIO(b"fake pdf content")
        response = self.client.post(
            "/api/v1/resumes/normalize",
            files={"file": ("resume.pdf", file_content, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "normalized" in data["data"]
