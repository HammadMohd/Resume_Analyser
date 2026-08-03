"""Upload schemas — Pydantic models for upload request/response contracts.

This module defines the data shapes that flow between the API layer
and the service layer. These schemas enforce the contract:
what the client sends, what the server returns.

Responsibilities:
    - Defining request/response shapes
    - Enforcing field types and constraints
    - Providing API documentation via JSON Schema

NOT responsible for:
    - Business logic or validation rules
    - File processing or storage decisions
    - HTTP status codes or headers
"""

from datetime import datetime

from pydantic import BaseModel, Field


class UploadMetadata(BaseModel):
    """Metadata about an uploaded file.

    Contains all information needed to track and reference
    the uploaded file in subsequent operations.
    """

    id: str = Field(..., description="Unique identifier for this upload")
    original_filename: str = Field(..., description="Original filename from client")
    stored_filename: str = Field(..., description="UUID-based filename on disk")
    content_type: str = Field(..., description="MIME type of the file")
    size_bytes: int = Field(..., description="File size in bytes")
    upload_timestamp: datetime = Field(..., description="UTC timestamp when upload completed")


class UploadResponse(BaseModel):
    """Response schema for a successful file upload.

    Wraps success status, message, and file metadata.
    """

    success: bool = Field(..., description="Whether the upload succeeded")
    message: str = Field(..., description="Human-readable status message")
    data: UploadMetadata = Field(..., description="File metadata")


class ErrorResponse(BaseModel):
    """Standard error response schema.

    Used by all endpoints to return structured errors.
    The errors list provides detailed validation failures
    when applicable.
    """

    success: bool = Field(..., description="Always false for errors")
    message: str = Field(..., description="Human-readable error summary")
    errors: list[str] | None = Field(
        default=None, description="Detailed list of validation failures"
    )
