"""Tests for extraction engine — Phase 5.

Tests NER extraction, skills extraction, and the extract endpoint.
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.parser.extraction_engine import ExtractionEngine
from backend.parser.ner_extractor import NERExtractor
from backend.parser.skills_extractor import SkillsExtractor
from backend.schemas.extraction import ExtractionResult

# ── NER Extractor Tests ─────────────────────────────────────────────


class TestNERExtractor:
    """Test NER entity extraction."""

    def setup_method(self):
        self.extractor = NERExtractor()

    def test_extract_emails(self):
        text = "Contact john@example.com or jane@test.org"
        emails = self.extractor.extract_emails(text)
        assert "john@example.com" in emails
        assert "jane@test.org" in emails

    def test_extract_phones(self):
        text = "Call me at 555-123-4567 or (555) 987-6543"
        phones = self.extractor.extract_phones(text)
        assert len(phones) >= 2

    def test_extract_linkedin(self):
        text = "linkedin.com/in/johndoe"
        linkedin = self.extractor.extract_linkedin(text)
        assert len(linkedin) == 1
        assert "johndoe" in linkedin[0]

    def test_extract_github(self):
        text = "github.com/johndoe"
        github = self.extractor.extract_github(text)
        assert len(github) == 1
        assert "johndoe" in github[0]

    def test_extract_dates(self):
        text = "Jan 2020 - Present\n2018 - 2020"
        dates = self.extractor.extract_dates(text)
        assert len(dates) >= 1

    def test_extract_urls(self):
        text = "Visit https://example.com for more"
        urls = self.extractor.extract_urls(text)
        assert len(urls) == 1
        assert "example.com" in urls[0]

    def test_extract_entities_combined(self):
        text = """John Doe
john@example.com
555-123-4567
linkedin.com/in/johndoe
github.com/johndoe"""
        entities = self.extractor.extract_entities(text)
        assert len(entities["emails"]) == 1
        assert len(entities["phones"]) == 1
        assert len(entities["linkedin"]) == 1
        assert len(entities["github"]) == 1

    def test_empty_text(self):
        entities = self.extractor.extract_entities("")
        assert entities["emails"] == []
        assert entities["phones"] == []


# ── Skills Extractor Tests ──────────────────────────────────────────


class TestSkillsExtractor:
    """Test skills extraction."""

    def setup_method(self):
        self.extractor = SkillsExtractor()

    def test_extract_python_skill(self):
        text = "Proficient in Python and JavaScript"
        skills = self.extractor.extract_skills(text)
        skill_names = [s["skill"] for s in skills]
        assert "python" in skill_names
        assert "javascript" in skill_names

    def test_extract_framework_skills(self):
        text = "Experience with React, Django, and FastAPI"
        skills = self.extractor.extract_skills(text)
        skill_names = [s["skill"] for s in skills]
        assert "react" in skill_names
        assert "django" in skill_names
        assert "fastapi" in skill_names

    def test_extract_cloud_skills(self):
        text = "AWS and Docker experience"
        skills = self.extractor.extract_skills(text)
        skill_names = [s["skill"] for s in skills]
        assert "aws" in skill_names
        assert "docker" in skill_names

    def test_skills_by_category(self):
        text = "Python, React, AWS, PostgreSQL"
        categories = self.extractor.extract_skills_by_category(text)
        assert "programming_languages" in categories
        assert "web_frameworks" in categories

    def test_detect_proficiency(self):
        text = "Expert in Python with 5+ years experience"
        level = self.extractor.detect_proficiency(text, "python")
        assert level in ["expert", "advanced"]

    def test_empty_text(self):
        skills = self.extractor.extract_skills("")
        assert skills == []


# ── Extraction Engine Tests ─────────────────────────────────────────


class TestExtractionEngine:
    """Test extraction coordinator."""

    def setup_method(self):
        self.engine = ExtractionEngine()

    def test_extract_returns_result(self):
        text = """John Doe
john@example.com
555-123-4567

Skills: Python, React, AWS"""
        result = self.engine.extract(text, "test.pdf")
        assert isinstance(result, ExtractionResult)
        assert result.filename == "test.pdf"
        assert len(result.emails) >= 1
        assert len(result.skills) >= 1

    def test_extract_preserves_raw_text(self):
        text = "Python developer"
        result = self.engine.extract(text, "test.pdf")
        assert result.raw_text == text

    def test_extraction_time_positive(self):
        text = "Python developer"
        result = self.engine.extract(text, "test.pdf")
        assert result.extraction_time_ms >= 0

    def test_extract_skills_categorized(self):
        text = "Python, React, Docker, PostgreSQL"
        result = self.engine.extract(text, "test.pdf")
        assert len(result.skill_categories) >= 1

    def test_empty_text(self):
        result = self.engine.extract("", "test.pdf")
        assert result.emails == []
        assert result.skills == []


# ── Schema Tests ────────────────────────────────────────────────────


class TestExtractionSchema:
    """Test extraction schema validation."""

    def test_minimal_extraction(self):
        result = ExtractionResult(filename="test.pdf")
        assert result.filename == "test.pdf"
        assert result.entities == []

    def test_full_extraction(self):
        result = ExtractionResult(
            filename="test.pdf",
            emails=["test@example.com"],
            phones=["555-123-4567"],
            skills=[],
        )
        assert result.emails == ["test@example.com"]


# ── Extract Endpoint Tests ──────────────────────────────────────────


class TestExtractEndpoint:
    """Test POST /api/v1/resumes/extract endpoint."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_extract_requires_file(self):
        response = self.client.post("/api/v1/resumes/extract")
        assert response.status_code == 422

    @patch("backend.api.routes.resume.ExtractionEngine")
    @patch("backend.api.routes.resume.StructuredParser")
    @patch("backend.api.routes.resume.ResumeParser")
    @patch("backend.api.routes.resume.UploadService")
    def test_extract_returns_200(self, MockUpload, MockParser, MockStructured, MockExtraction):
        # Mock upload
        mock_upload = MagicMock()
        mock_upload.upload_resume = AsyncMock(
            return_value={
                "data": {
                    "stored_filename": "abc123.pdf",
                    "original_filename": "resume.pdf",
                    "upload_timestamp": MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
                }
            }
        )
        MockUpload.return_value = mock_upload

        # Mock parser
        mock_parser = MagicMock()
        mock_parser.parse.return_value = MagicMock(raw_text="Python developer")
        MockParser.return_value = mock_parser

        # Mock structured parser
        mock_structured = MagicMock()
        mock_structured.parse_resume.return_value = MagicMock(
            model_dump=lambda: {"filename": "resume.pdf"}
        )
        MockStructured.return_value = mock_structured

        # Mock extraction engine
        mock_extraction = MagicMock()
        mock_extraction.extract.return_value = ExtractionResult(
            filename="resume.pdf",
            emails=["test@example.com"],
            skills=[],
        )
        MockExtraction.return_value = mock_extraction

        file_content = io.BytesIO(b"fake pdf content")
        response = self.client.post(
            "/api/v1/resumes/extract",
            files={"file": ("resume.pdf", file_content, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "extraction" in data["data"]
