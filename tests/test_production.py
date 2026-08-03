"""Tests for production features (rate limiting, metrics)."""

import time

import pytest
from fastapi.testclient import TestClient

from backend.middleware.rate_limit import disable_rate_limiting, enable_rate_limiting


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    def test_allows_requests_within_limit(self, client: TestClient):
        """Requests within limit should succeed."""
        enable_rate_limiting()
        try:
            for _ in range(5):
                response = client.get("/health")
                assert response.status_code == 200
        finally:
            disable_rate_limiting()

    def test_rate_limit_returns_429(self, client: TestClient):
        """Exceeding rate limit should return 429."""
        enable_rate_limiting()
        try:
            # Make many requests quickly to trigger rate limit
            for _ in range(100):
                client.get("/health")

            response = client.get("/health")
            assert response.status_code == 429
            data = response.json()
            assert data["success"] is False
            assert "Rate limit exceeded" in data["error"]
        finally:
            disable_rate_limiting()


class TestMetrics:
    """Tests for metrics endpoint."""

    def test_metrics_endpoint_returns_200(self, client: TestClient):
        """Metrics endpoint should return 200."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "uptime_human" in data
        assert "metrics" in data

    def test_metrics_has_uptime(self, client: TestClient):
        """Metrics should include uptime."""
        response = client.get("/metrics")
        data = response.json()
        assert data["uptime_seconds"] > 0

    def test_increment_metric(self, client: TestClient):
        """Can increment custom metrics."""
        response = client.post("/metrics/test_counter")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metric"] == "test_counter"


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, client: TestClient):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_status(self, client: TestClient):
        """Health response should have status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_has_version(self, client: TestClient):
        """Health response should have version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data

    def test_health_has_environment(self, client: TestClient):
        """Health response should have environment."""
        response = client.get("/health")
        data = response.json()
        assert "environment" in data
