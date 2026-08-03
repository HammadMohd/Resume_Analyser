"""Unit tests for ValidationService."""

import io

import pytest
from fastapi import UploadFile

from backend.exceptions import FileValidationError
from backend.services.validation_service import ValidationService


@pytest.fixture
def service() -> ValidationService:
    return ValidationService()


def make_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    """Create an UploadFile with the given content type."""
    tmp = io.BytesIO(content)
    tmp.name = filename
    return UploadFile(filename=filename, file=tmp, headers={"content-type": content_type})


class TestValidationService:
    """Tests for file validation logic."""

    @pytest.mark.asyncio
    async def test_valid_pdf(self, service: ValidationService):
        """Valid PDF should pass validation."""
        file = make_file("resume.pdf", b"%PDF-1.4 content", "application/pdf")
        await service.validate(file)

    @pytest.mark.asyncio
    async def test_valid_docx(self, service: ValidationService):
        """Valid DOCX should pass validation."""
        file = make_file("resume.docx", b"PK content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        await service.validate(file)

    @pytest.mark.asyncio
    async def test_empty_file_rejected(self, service: ValidationService):
        """Empty file should raise FileValidationError."""
        file = make_file("empty.pdf", b"", "application/pdf")
        with pytest.raises(FileValidationError) as exc_info:
            await service.validate(file)
        assert "File is empty" in exc_info.value.errors

    @pytest.mark.asyncio
    async def test_wrong_extension_rejected(self, service: ValidationService):
        """Wrong extension should raise FileValidationError."""
        file = make_file("resume.txt", b"hello", "text/plain")
        with pytest.raises(FileValidationError) as exc_info:
            await service.validate(file)
        assert any("extension" in e.lower() for e in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_wrong_mime_type_rejected(self, service: ValidationService):
        """Wrong MIME type should raise FileValidationError."""
        file = make_file("resume.pdf", b"%PDF-1.4 content", "text/plain")
        with pytest.raises(FileValidationError) as exc_info:
            await service.validate(file)
        assert any("MIME" in e for e in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_multiple_errors(self, service: ValidationService):
        """Multiple validation errors should all be reported."""
        file = make_file("bad.txt", b"hello", "text/plain")
        with pytest.raises(FileValidationError) as exc_info:
            await service.validate(file)
        assert len(exc_info.value.errors) >= 2

    @pytest.mark.asyncio
    async def test_no_filename_rejected(self, service: ValidationService):
        """File with no extension should be rejected."""
        file = make_file("resume", b"content", "application/pdf")
        with pytest.raises(FileValidationError) as exc_info:
            await service.validate(file)
        assert any("extension" in e.lower() for e in exc_info.value.errors)
