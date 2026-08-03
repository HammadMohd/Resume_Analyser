"""Integration test — full upload pipeline end-to-end.

Tests the complete flow:
    Client → Router → ValidationService → StorageService → Response
"""

import json

import pytest
from fastapi.testclient import TestClient


class TestUploadPipeline:
    """End-to-end tests for the upload pipeline."""

    def test_complete_upload_flow(self, client: TestClient):
        """Test full pipeline: upload → validate → store → metadata → response."""
        # Step 1: Upload a valid PDF
        files = {"file": ("resume.pdf", b"%PDF-1.4 resume content", "application/pdf")}
        response = client.post("/api/v1/resumes/", files=files)

        # Step 2: Verify response
        assert response.status_code == 200
        data = response.json()

        # Step 3: Verify success
        assert data["success"] is True
        assert data["message"] == "File uploaded and stored successfully"

        # Step 4: Verify metadata structure
        metadata = data["data"]
        assert "id" in metadata
        assert "original_filename" in metadata
        assert "stored_filename" in metadata
        assert "content_type" in metadata
        assert "size_bytes" in metadata
        assert "upload_timestamp" in metadata

        # Step 5: Verify values
        assert metadata["original_filename"] == "resume.pdf"
        assert metadata["content_type"] == "application/pdf"
        assert metadata["size_bytes"] == len(b"%PDF-1.4 resume content")
        assert metadata["stored_filename"].endswith(".pdf")
        assert "-" in metadata["id"]  # UUID format

    def test_validation_blocks_invalid_files(self, client: TestClient):
        """Test that validation rejects invalid files before storage."""
        # Step 1: Try to upload invalid file
        files = {"file": ("bad.txt", b"hello", "text/plain")}
        response = client.post("/api/v1/resumes/", files=files)

        # Step 2: Verify rejection
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "errors" in data
        assert len(data["errors"]) > 0

    def test_multiple_uploads_create_unique_files(self, client: TestClient):
        """Test that multiple uploads create different stored files."""
        # Step 1: Upload twice
        files1 = {"file": ("resume.pdf", b"content1", "application/pdf")}
        files2 = {"file": ("resume.pdf", b"content2", "application/pdf")}

        r1 = client.post("/api/v1/resumes/", files=files1)
        r2 = client.post("/api/v1/resumes/", files=files2)

        # Step 2: Verify both succeed
        assert r1.status_code == 200
        assert r2.status_code == 200

        # Step 3: Verify different stored filenames
        data1 = r1.json()["data"]
        data2 = r2.json()["data"]
        assert data1["stored_filename"] != data2["stored_filename"]
        assert data1["id"] != data2["id"]

    def test_docx_upload_flow(self, client: TestClient):
        """Test DOCX upload follows same pipeline."""
        files = {"file": ("resume.docx", b"PK docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        response = client.post("/api/v1/resumes/", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["original_filename"] == "resume.docx"
        assert data["data"]["stored_filename"].endswith(".docx")

    def test_upload_metadata_is_valid_json(self, client: TestClient):
        """Test response is valid JSON with correct types."""
        files = {"file": ("resume.pdf", b"%PDF-1.4 content", "application/pdf")}
        response = client.post("/api/v1/resumes/", files=files)

        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        assert isinstance(data["data"], dict)
        assert isinstance(data["data"]["id"], str)
        assert isinstance(data["data"]["size_bytes"], int)

    def test_error_response_is_valid_json(self, client: TestClient):
        """Test error response is valid JSON with correct structure."""
        files = {"file": ("bad.txt", b"hello", "text/plain")}
        response = client.post("/api/v1/resumes/", files=files)

        data = response.json()
        assert isinstance(data, dict)
        assert data["success"] is False
        assert isinstance(data["message"], str)
        assert isinstance(data["errors"], list)
