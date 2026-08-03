"""Validation service — checks if uploaded files meet acceptance criteria.

This module owns all file validation logic. It is the first gate
in the upload pipeline — rejecting bad files before they reach storage.

Responsibilities:
    - Checking file extension (.pdf, .docx only)
    - Checking MIME type matches extension
    - Rejecting empty files
    - Enforcing maximum file size limits

NOT responsible for:
    - Storing files (belongs to StorageService)
    - Parsing file content (belongs to parser module)
    - Building response metadata (belongs to UploadService)

Architecture position:
    Client → Router → UploadService → **ValidationService** → StorageService

Why validation is separate:
    - Can be tested without HTTP or storage
    - Can swap validation rules without touching other services
    - Clear responsibility: one service, one job
"""

from fastapi import UploadFile

from backend.config.settings import settings
from backend.exceptions import FileValidationError
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Allowed file extensions (without dot)
ALLOWED_EXTENSIONS = {"pdf", "docx"}

# Allowed MIME types (some clients send wrong MIME, so we check both)
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# Extension to MIME mapping for cross-checking
EXTENSION_TO_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class ValidationService:
    """Validates uploaded files against acceptance criteria.

    Runs a series of checks before allowing a file to proceed
    to storage. Each check is independent and returns a specific
    error message if it fails.
    """

    async def validate(self, file: UploadFile) -> None:
        """Run all validation checks on an uploaded file.

        Checks run in order:
            1. File is not empty
            2. File extension is allowed
            3. MIME type is allowed
            4. MIME type matches extension
            5. File size is within limit

        Args:
            file: The uploaded file to validate.

        Raises:
            ValidationError: If any check fails. Contains a list
                of specific error messages.
        """
        logger.info("Validation started for %s", file.filename)
        errors: list[str] = []

        # Check 1: File is not empty
        if await self._is_empty(file):
            errors.append("File is empty")
            logger.warning("Validation check failed: file is empty")

        # Check 2: Extension is allowed
        if not self._has_valid_extension(file):
            ext = self._get_extension(file)
            errors.append(
                f"Invalid file extension '{ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
            logger.warning("Validation check failed: invalid extension '%s'", ext)

        # Check 3: MIME type is allowed
        if not self._has_valid_mime_type(file):
            errors.append(
                f"Invalid MIME type '{file.content_type}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            )
            logger.warning("Validation check failed: invalid MIME type '%s'", file.content_type)

        # Check 4: MIME matches extension
        if not self._mime_matches_extension(file):
            ext = self._get_extension(file)
            expected_mime = EXTENSION_TO_MIME.get(ext, "unknown")
            errors.append(
                f"MIME type '{file.content_type}' does not match "
                f"extension '{ext}' (expected '{expected_mime}')"
            )
            logger.warning(
                "Validation check failed: MIME '%s' does not match extension '%s'",
                file.content_type,
                ext,
            )

        # Check 5: File size is within limit
        if not await self._is_within_size_limit(file):
            max_mb = settings.max_upload_size_mb
            errors.append(f"File exceeds maximum size of {max_mb} MB")
            logger.warning("Validation check failed: file exceeds size limit")

        # If any errors, raise with all of them
        if errors:
            logger.error("Validation failed for %s: %d errors", file.filename, len(errors))
            raise FileValidationError("File validation failed", errors)

        logger.info("Validation passed for %s", file.filename)

    async def _is_empty(self, file: UploadFile) -> bool:
        """Check if file has no content.

        Reads a small chunk to detect empty files without loading
        the entire file into memory.
        """
        chunk = await file.read(1)
        await file.seek(0)  # Reset pointer after reading
        return len(chunk) == 0

    def _has_valid_extension(self, file: UploadFile) -> bool:
        """Check if file extension is in allowed list."""
        ext = self._get_extension(file)
        return ext in ALLOWED_EXTENSIONS

    def _has_valid_mime_type(self, file: UploadFile) -> bool:
        """Check if MIME type is in allowed list."""
        return file.content_type in ALLOWED_MIME_TYPES

    def _mime_matches_extension(self, file: UploadFile) -> bool:
        """Check if MIME type matches the file extension.

        Some clients send wrong MIME types. We cross-check
        to catch mismatches early.
        """
        ext = self._get_extension(file)
        expected_mime = EXTENSION_TO_MIME.get(ext)
        if expected_mime is None:
            return False  # Unknown extension, already caught by extension check
        return file.content_type == expected_mime

    async def _is_within_size_limit(self, file: UploadFile) -> bool:
        """Check if file size is within configured limit.

        Reads the entire file to get accurate size. For very large
        files, this may use disk spooling (handled by UploadFile).
        """
        content = await file.read()
        await file.seek(0)  # Reset pointer after reading
        size_bytes = len(content)
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        return size_bytes <= max_bytes

    @staticmethod
    def _get_extension(file: UploadFile) -> str:
        """Extract file extension without the dot.

        Returns lowercase extension (e.g., 'pdf', 'docx').
        Returns empty string if no extension found.
        """
        if not file.filename:
            return ""
        return file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
