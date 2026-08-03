"""Custom exceptions — application-wide error types.

This module defines all custom exceptions used across the application.
Each exception represents a specific failure mode with structured
error information.

Responsibilities:
    - Defining exception hierarchy
    - Providing structured error details
    - Enabling consistent error handling

NOT responsible for:
    - HTTP status codes (belongs to router layer)
    - Error response formatting (belongs to schemas)
    - Logging (each service handles its own logging)

Usage:
    raise FileValidationError("Invalid extension", errors=["..."])

    try:
        await service.upload(file)
    except FileValidationError as e:
        return JSONResponse(status_code=422, content=e.to_dict())
"""


class AppException(Exception):
    """Base exception for all application errors.

    All custom exceptions inherit from this. Provides:
    - Consistent error message format
    - Structured error details
    - Easy conversion to API response
    """

    def __init__(
        self,
        message: str,
        errors: list[str] | None = None,
        status_code: int = 500,
    ) -> None:
        self.message = message
        self.errors = errors or []
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API response."""
        return {
            "success": False,
            "message": self.message,
            "errors": self.errors if self.errors else None,
        }


class FileValidationError(AppException):
    """Raised when file validation fails.

    Attributes:
        message: Human-readable error description.
        errors: List of specific validation failures.
    """

    def __init__(
        self,
        message: str = "File validation failed",
        errors: list[str] | None = None,
    ) -> None:
        super().__init__(message=message, errors=errors, status_code=422)


class FileStorageError(AppException):
    """Raised when file storage fails.

    Attributes:
        message: Human-readable error description.
    """

    def __init__(self, message: str = "File storage failed") -> None:
        super().__init__(message=message, status_code=500)


class FileTooLargeError(AppException):
    """Raised when file exceeds size limit.

    Attributes:
        message: Human-readable error description.
        max_size_mb: Maximum allowed size in MB.
    """

    def __init__(
        self,
        message: str = "File too large",
        max_size_mb: int = 10,
    ) -> None:
        super().__init__(message=message, status_code=413)
        self.max_size_mb = max_size_mb


class FileEmptyError(AppException):
    """Raised when uploaded file is empty."""

    def __init__(self, message: str = "File is empty") -> None:
        super().__init__(message=message, status_code=422)


class UnsupportedFileTypeError(AppException):
    """Raised when file type is not supported.

    Attributes:
        message: Human-readable error description.
        allowed_types: List of allowed file extensions.
    """

    def __init__(
        self,
        message: str = "Unsupported file type",
        allowed_types: list[str] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=422)
        self.allowed_types = allowed_types or []
