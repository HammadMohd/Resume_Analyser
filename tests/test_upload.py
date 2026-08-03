"""Integration tests for resume upload endpoint."""

from fastapi.testclient import TestClient


class TestUploadEndpoint:
    """Tests for POST /api/v1/resumes/ endpoint."""

    def test_valid_pdf_upload(self, client: TestClient):
        """Valid PDF should return 200 with metadata."""
        files = {"file": ("resume.pdf", b"%PDF-1.4 content", "application/pdf")}
        response = client.post("/api/v1/resumes/", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["original_filename"] == "resume.pdf"
        assert "id" in data["data"]
        assert "stored_filename" in data["data"]
        assert "upload_timestamp" in data["data"]

    def test_valid_docx_upload(self, client: TestClient):
        """Valid DOCX should return 200 with metadata."""
        docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        files = {"file": ("resume.docx", b"PK content", docx_mime)}
        response = client.post("/api/v1/resumes/", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["original_filename"] == "resume.docx"

    def test_wrong_extension_rejected(self, client: TestClient):
        """Wrong extension should return 422."""
        files = {"file": ("resume.txt", b"hello", "text/plain")}
        response = client.post("/api/v1/resumes/", files=files)
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "errors" in data

    def test_empty_file_rejected(self, client: TestClient):
        """Empty file should return 422."""
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        response = client.post("/api/v1/resumes/", files=files)
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert any("empty" in e.lower() for e in data["errors"])

    def test_wrong_mime_type_rejected(self, client: TestClient):
        """Wrong MIME type should return 422."""
        files = {"file": ("resume.pdf", b"%PDF-1.4 content", "text/plain")}
        response = client.post("/api/v1/resumes/", files=files)
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    def test_no_file_rejected(self, client: TestClient):
        """No file should return 422."""
        response = client.post("/api/v1/resumes/")
        assert response.status_code == 422

    def test_response_schema(self, client: TestClient):
        """Response should match expected schema."""
        files = {"file": ("resume.pdf", b"%PDF-1.4 content", "application/pdf")}
        response = client.post("/api/v1/resumes/", files=files)
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "id" in data["data"]
        assert "original_filename" in data["data"]
        assert "stored_filename" in data["data"]
        assert "content_type" in data["data"]
        assert "size_bytes" in data["data"]
        assert "upload_timestamp" in data["data"]
