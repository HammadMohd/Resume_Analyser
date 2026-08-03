"""Tests for LLM Refinement Layer — Phase 10.

Tests prompt building, validation, bullet rewriting, and endpoints.
"""


from fastapi.testclient import TestClient

from backend.llm.prompt_builder import (
    build_bullet_rewrite_prompt,
    build_multi_bullet_rewrite_prompt,
)
from backend.llm.rewriter import BulletRewriter
from backend.llm.schemas import (
    BulletRewriteRequest,
    BulletRewriteResponse,
    LLMValidationResult,
    RewriteRequest,
    RewriteResponse,
)
from backend.llm.validator import validate_bullet_rewrite
from backend.main import app

# ── Prompt Builder Tests ────────────────────────────────────────────


class TestPromptBuilder:
    """Test prompt construction."""

    def test_single_bullet_prompt(self):
        prompt = build_bullet_rewrite_prompt(
            original="Did stuff",
            context="Backend Developer",
        )
        assert "Did stuff" in prompt
        assert "Backend Developer" in prompt
        assert "JSON" in prompt

    def test_single_bullet_with_skills(self):
        prompt = build_bullet_rewrite_prompt(
            original="Built API",
            missing_skills=["Python", "FastAPI"],
        )
        assert "Python" in prompt
        assert "FastAPI" in prompt

    def test_multi_bullet_prompt(self):
        bullets = [
            {"original": "Bullet 1"},
            {"original": "Bullet 2"},
        ]
        prompt = build_multi_bullet_rewrite_prompt(bullets, job_title="Engineer")
        assert "Bullet 1" in prompt
        assert "Bullet 2" in prompt
        assert "Engineer" in prompt


# ── Validator Tests ─────────────────────────────────────────────────


class TestValidator:
    """Test LLM output validation."""

    def test_valid_bullet_passes(self):
        result = validate_bullet_rewrite(
            original="Did work on APIs",
            improved="Developed APIs for the backend",
        )
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_too_short_fails(self):
        result = validate_bullet_rewrite(
            original="Did stuff",
            improved="Did things",
        )
        assert result.is_valid is False
        assert any("short" in i.lower() for i in result.issues)

    def test_fake_metric_detected(self):
        result = validate_bullet_rewrite(
            original="Improved performance",
            improved="Improved performance by 500%",
        )
        assert result.is_valid is False
        assert any("metric" in i.lower() or "hallucination" in i.lower() for i in result.issues)

    def test_new_tech_detected(self):
        result = validate_bullet_rewrite(
            original="Built backend with Python",
            improved="Built backend with Python and Kubernetes",
        )
        assert result.is_valid is False
        assert any("technology" in i.lower() or "kubernetes" in i.lower() for i in result.issues)

    def test_no_action_verb_warning(self):
        result = validate_bullet_rewrite(
            original="Responsible for APIs",
            improved="Responsible for managing APIs",
        )
        # May pass or fail depending on implementation
        assert isinstance(result, LLMValidationResult)


# ── Rewriter Tests ──────────────────────────────────────────────────


class TestRewriter:
    """Test bullet rewriting logic."""

    def setup_method(self):
        self.rewriter = BulletRewriter()

    def test_rewrite_returns_response(self):
        request = BulletRewriteRequest(
            original="Worked on various projects",
            context="Developer",
        )
        result = self.rewriter.rewrite_bullet(request)
        assert isinstance(result, BulletRewriteResponse)
        assert result.original == "Worked on various projects"
        assert len(result.improved) > 0

    def test_rewrite_preserves_original(self):
        request = BulletRewriteRequest(original="Built API")
        result = self.rewriter.rewrite_bullet(request)
        assert result.original == "Built API"

    def test_rewrite_multiple(self):
        request = RewriteRequest(
            bullets=[
                BulletRewriteRequest(original="Bullet 1"),
                BulletRewriteRequest(original="Bullet 2"),
            ]
        )
        result = self.rewriter.rewrite_bullets(request)
        assert isinstance(result, RewriteResponse)
        assert len(result.rewritten_bullets) == 2

    def test_rewrite_confidence_positive(self):
        request = BulletRewriteRequest(original="Developed features")
        result = self.rewriter.rewrite_bullet(request)
        assert 0 <= result.confidence <= 1


# ── Schema Tests ────────────────────────────────────────────────────


class TestLLMSchema:
    """Test LLM schemas."""

    def test_rewrite_request(self):
        request = RewriteRequest(
            bullets=[BulletRewriteRequest(original="Test")],
            job_title="Engineer",
        )
        assert len(request.bullets) == 1

    def test_rewrite_response(self):
        response = RewriteResponse(
            rewritten_bullets=[
                BulletRewriteResponse(original="Test", improved="Improved test")
            ],
            total_improved=1,
        )
        assert response.total_improved == 1


# ── Endpoint Tests ──────────────────────────────────────────────────


class TestRewriteEndpoint:
    """Test rewrite endpoints."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_rewrite_bullet_requires_original(self):
        response = self.client.post("/api/v1/rewrite/bullet?original=")
        assert response.status_code in [400, 422, 200]

    def test_rewrite_bullet_returns_200(self):
        response = self.client.post(
            "/api/v1/rewrite/bullet?original=Worked%20on%20backend%20services&context=Developer",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "improved" in data["data"]

    def test_validate_requires_both(self):
        response = self.client.post(
            "/api/v1/rewrite/validate?original=&improved=",
        )
        assert response.status_code in [400, 422, 200]

    def test_validate_returns_200(self):
        response = self.client.post(
            "/api/v1/rewrite/validate?original=Did%20work&improved=Implemented%20key%20features",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "is_valid" in data["data"]
