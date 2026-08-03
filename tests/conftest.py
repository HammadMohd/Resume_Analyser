"""Test configuration — pytest fixtures for testing."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Return sample PDF content for testing."""
    return b"%PDF-1.4 fake resume content"


@pytest.fixture
def sample_docx_bytes() -> bytes:
    """Return sample DOCX content for testing."""
    return b"PK\x03\x04fake docx content"
