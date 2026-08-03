"""Storage service — handles writing files to disk with UUID filenames.

This module owns all file system operations for uploaded resumes.
It is the only module that should ever write to the storage directory.

Responsibilities:
    - Saving file bytes to disk
    - Generating unique filenames (UUID-based)
    - Retrieving file paths for stored files
    - Ensuring no file overwrites occur

NOT responsible for:
    - Validating files (belongs to ValidationService)
    - Building metadata responses (belongs to UploadService)
    - Knowing about FastAPI, HTTP, or UploadFile objects
    - Understanding what the files contain (no parsing)
    - ATS scoring, OCR, or LLM operations

Architecture position:
    Client → Router → UploadService → **StorageService** → Filesystem

Design principle:
    This service operates on raw bytes and paths. It never imports
    FastAPI types or knows about HTTP requests. This makes it
    testable without a running server and reusable from CLI tools,
    background queues, or test fixtures.
"""

import uuid
from pathlib import Path

from backend.config.settings import settings
from backend.exceptions import FileStorageError
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Manages file storage on the local filesystem.

    All file operations go through this service. It ensures:
    - Unique filenames via UUID generation
    - No accidental file overwrites
    - Clean separation between storage mechanics and business logic

    This service is injected into UploadService, never the reverse.
    Dependencies flow downward: UploadService → StorageService → Filesystem.
    """

    def __init__(self) -> None:
        """Initialize storage service with configured upload directory."""
        self.storage_dir = Path(settings.upload_dir) / "resumes"

    async def store_file(self, file_bytes: bytes, original_filename: str) -> Path:
        """Store a file on disk with a UUID-based filename.

        The original filename is preserved in metadata but never used
        for the stored path. This prevents:
        - Path traversal attacks
        - Filename collisions
        - Overwriting existing files

        Args:
            file_bytes: The raw file content as bytes.
            original_filename: The client-provided filename (used only
                               for metadata, not for storage path).

        Returns:
            Path: The absolute path where the file was stored.

        Raises:
            StorageError: If file cannot be written to disk.
        """
        logger.info("Storage started for %s (%d bytes)", original_filename, len(file_bytes))

        # Step 1: Ensure storage directory exists
        self._ensure_directory()
        logger.debug("Storage directory ready: %s", self.storage_dir)

        # Step 2: Generate unique filename
        stored_filename = self._generate_filename(original_filename)
        logger.debug("Generated filename: %s -> %s", original_filename, stored_filename)

        # Step 3: Write file to disk
        file_path = self.storage_dir / stored_filename
        try:
            file_path.write_bytes(file_bytes)
            logger.info(
                "Storage successful: %s -> %s",
                original_filename,
                stored_filename,
            )
        except OSError as e:
            logger.error(
                "Storage failed for %s: %s",
                original_filename,
                e,
            )
            raise FileStorageError(f"Failed to store file: {e}") from e

        return file_path

    def _ensure_directory(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, original_filename: str) -> str:
        """Generate a UUID-based filename preserving the extension.

        Example:
            Input: "John_Resume.pdf"
            Output: "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf"

        Args:
            original_filename: The original filename from the client.

        Returns:
            UUID-based filename with original extension.
        """
        ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext}"
