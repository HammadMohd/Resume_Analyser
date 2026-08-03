"""Tests for frontend static file serving."""

import pytest
from fastapi.testclient import TestClient


class TestFrontend:
    """Tests for static file serving."""

    def test_index_html_served(self, client: TestClient):
        """Root URL should serve index.html."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Resume ATS Analyzer" in response.text

    def test_styles_css_served(self, client: TestClient):
        """styles.css should be accessible."""
        response = client.get("/styles.css")
        assert response.status_code == 200
        assert "box-sizing" in response.text

    def test_app_js_served(self, client: TestClient):
        """app.js should be accessible."""
        response = client.get("/app.js")
        assert response.status_code == 200
        assert "API_BASE" in response.text

    def test_health_check_still_works(self, client: TestClient):
        """Health endpoint should still work."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
