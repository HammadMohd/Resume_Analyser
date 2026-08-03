"""Upload service — orchestrates the resume upload pipeline.

This module owns the business logic for processing resume uploads.
It coordinates validation, storage, and metadata generation
without knowing the details of any individual step.

Responsibilities:
    - Orchestrating the upload pipeline (validate → store → respond)
    - Calling ValidationService to check file constraints
    - Calling StorageService to persist files to disk
    - Building UploadMetadata from storage results
    - Logging upload events (start, success, failure)

NOT responsible for:
    - Parsing resume content (belongs to parser module)
    - OCR or text extraction (belongs to ocr module)
    - ATS scoring or analysis (belongs to ats/scoring modules)
    - LLM integration (belongs to llm module)
    - HTTP request/response handling (belongs to router layer)

Architecture position:
    Client → Router → **UploadService** → StorageService → Filesystem
"""

import uuid
from datetime import datetime, timezone

from fastapi import UploadFile

from backend.services.storage_service import StorageService
from backend.services.validation_service import ValidationService
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class UploadService:
    """Orchestrates the resume upload pipeline.

    This service acts as the central coordinator for upload operations.
    It receives a file from the router, validates it, stores it,
    and returns metadata — without coupling to any infrastructure detail.

    The service never touches the filesystem directly.
    It delegates storage to StorageService and validation
    to ValidationService.
    """

    def __init__(self) -> None:
        """Initialize with injected dependencies."""
        self.validation_service = ValidationService()
        self.storage_service = StorageService()

    async def upload_resume(self, file: UploadFile) -> dict:
        """Process a resume upload through the full pipeline.

        Pipeline:
            1. Validate file (extension, MIME, size, emptiness)
            2. Store file to disk with UUID filename
            3. Build metadata response
            4. Return structured result

        Args:
            file: The uploaded file from FastAPI (UploadFile object).

        Returns:
            dict: Upload metadata including ID, filenames, size, timestamp.

        Raises:
            ValidationError: If file fails validation checks.
            StorageError: If file cannot be written to disk.
        """
        logger.info("Upload started: %s", file.filename)

        # Step 1: Validate
        logger.info("Running validation for %s", file.filename)
        await self.validation_service.validate(file)
        logger.info("Validation passed for %s", file.filename)

        # Step 2: Store file
        logger.info("Reading file content for %s", file.filename)
        content = await file.read()
        file_size = len(content)
        await file.seek(0)
        logger.info("File read complete: %s (%d bytes)", file.filename, file_size)

        logger.info("Storing file %s", file.filename)
        stored_path = await self.storage_service.store_file(
            file_bytes=content,
            original_filename=file.filename or "unknown",
        )
        logger.info("File stored: %s -> %s", file.filename, stored_path.name)

        # Step 3: Build metadata
        metadata = {
            "id": str(uuid.uuid4()),
            "original_filename": file.filename or "unknown",
            "stored_filename": stored_path.name,
            "content_type": file.content_type or "application/octet-stream",
            "size_bytes": file_size,
            "upload_timestamp": datetime.now(timezone.utc),
        }

        logger.info("Upload completed successfully: %s (ID: %s)", file.filename, metadata["id"])

        return {
            "success": True,
            "message": "File uploaded and stored successfully",
            "data": metadata,
        }
