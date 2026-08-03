"""Unit tests for StorageService."""

import pytest

from backend.services.storage_service import StorageService


@pytest.fixture
def service() -> StorageService:
    return StorageService()


class TestStorageService:
    """Tests for file storage logic."""

    @pytest.mark.asyncio
    async def test_store_file(self, service: StorageService):
        """Storing a file should return a path with UUID filename."""
        path = await service.store_file(
            file_bytes=b"test content",
            original_filename="resume.pdf",
        )
        assert path.exists()
        assert path.suffix == ".pdf"
        assert "-" in path.stem  # UUID contains dashes

    @pytest.mark.asyncio
    async def test_no_overwrite(self, service: StorageService):
        """Storing same filename twice should create different files."""
        path1 = await service.store_file(b"content1", "test.pdf")
        path2 = await service.store_file(b"content2", "test.pdf")
        assert path1 != path2

    @pytest.mark.asyncio
    async def test_extension_preserved(self, service: StorageService):
        """Original extension should be preserved in stored filename."""
        path = await service.store_file(b"content", "resume.docx")
        assert path.suffix == ".docx"

    @pytest.mark.asyncio
    async def test_directory_created(self, service: StorageService):
        """Storage directory should be created if not exists."""
        assert service.storage_dir.exists()
