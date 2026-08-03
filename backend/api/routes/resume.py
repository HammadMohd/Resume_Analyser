"""Resume upload router — HTTP layer for resume upload endpoints.

This router owns all resume-related endpoints under /api/v1/resumes.
It is the entry point for client requests and the only layer
that interacts with FastAPI request/response objects.

Responsibilities:
    - Defining HTTP endpoints (routes)
    - Extracting UploadFile from requests
    - Calling UploadService for business logic
    - Returning JSON responses

NOT responsible for:
    - Business logic or validation rules (belongs to UploadService)
    - File storage or filesystem operations (belongs to StorageService)
    - Resume parsing or content extraction (belongs to parser module)
    - ATS scoring or analysis (belongs to ats/scoring modules)

Architecture position:
    Client → **Resume Router** → UploadService → StorageService → Filesystem

Design principle:
    This router must stay thin. It does exactly three things:
    1. Extracts parameters from the HTTP request
    2. Calls the appropriate service
    3. Returns the service's response

    All business logic lives in UploadService.
"""

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from backend.exceptions import AppException, FileValidationError, FileStorageError
from backend.parser.resume_parser import ParseError, ResumeParser
from backend.parser.structured_parser import StructuredParser
from backend.parser.extraction_engine import ExtractionEngine
from backend.rules.rule_engine import RuleEngine
from backend.schemas.upload import UploadResponse
from backend.services.upload_service import UploadService
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


def get_upload_service() -> UploadService:
    """Dependency provider for UploadService.

    FastAPI calls this function to inject the service.
    Makes testing easy — just mock this dependency.
    """
    return UploadService()


@router.post("/", response_model=UploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    service: UploadService = Depends(get_upload_service),
) -> UploadResponse | JSONResponse:
    """Upload a resume file (PDF or DOCX).

    Accepts a multipart/form-data request with a single file field.
    The file is processed through the upload pipeline:
    validation → storage → metadata generation.

    Args:
        file: The resume file to upload (PDF or DOCX).
        service: UploadService injected via dependency injection.

    Returns:
        UploadResponse: Success status with file metadata.
        JSONResponse: Error response if validation fails (422).
    """
    try:
        result = await service.upload_resume(file)
        return UploadResponse(**result)

    except FileValidationError as e:
        logger.warning("Validation failed for %s: %s", file.filename, e.message)
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict(),
        )

    except FileStorageError as e:
        logger.error("Storage failed for %s: %s", file.filename, e.message)
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict(),
        )

    except AppException as e:
        logger.error("Application error for %s: %s", file.filename, e.message)
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict(),
        )

    except Exception as e:
        logger.exception("Unexpected error for %s: %s", file.filename, str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "errors": None,
            },
        )


@router.post("/parse")
async def parse_resume(
    file: UploadFile = File(...),
) -> JSONResponse:
    """Parse a resume file and extract structured content.

    Uploads, validates, stores, and parses the resume in one call.
    Returns extracted text with coordinates and layout information.

    Args:
        file: The resume file to parse (PDF or DOCX).

    Returns:
        JSONResponse: Parsed resume content with metadata.
    """
    upload_service = UploadService()
    parser = ResumeParser()

    try:
        # Step 1: Upload and store
        upload_result = await upload_service.upload_resume(file)
        upload_data = upload_result["data"]
        # Convert datetime to string for JSON serialization
        upload_data["upload_timestamp"] = upload_data["upload_timestamp"].isoformat()
        stored_filename = upload_data["stored_filename"]

        # Step 2: Parse the stored file
        file_path = f"uploads/resumes/{stored_filename}"
        parsed = parser.parse(file_path, file.filename or "unknown")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Resume parsed successfully",
                "data": {
                    "upload": upload_data,
                    "parsed": parsed.model_dump(),
                },
            },
        )

    except FileValidationError as e:
        return JSONResponse(status_code=e.status_code, content=e.to_dict())

    except ParseError as e:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": f"Parsing failed: {e.message}",
                "errors": None,
            },
        )

    except Exception as e:
        logger.exception("Parse error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "errors": None,
            },
        )


@router.post("/normalize")
async def normalize_resume(
    file: UploadFile = File(...),
) -> JSONResponse:
    """Parse and normalize a resume into standard JSON format.

    Uploads, validates, stores, parses, and normalizes the resume.
    Returns structured resume with sections, contact, experience, etc.

    Args:
        file: The resume file to normalize (PDF or DOCX).

    Returns:
        JSONResponse: Normalized resume data.
    """
    upload_service = UploadService()
    parser = ResumeParser()
    structured_parser = StructuredParser()

    try:
        # Step 1: Upload and store
        upload_result = await upload_service.upload_resume(file)
        upload_data = upload_result["data"]
        upload_data["upload_timestamp"] = upload_data["upload_timestamp"].isoformat()
        stored_filename = upload_data["stored_filename"]

        # Step 2: Parse the stored file
        file_path = f"uploads/resumes/{stored_filename}"
        parsed = parser.parse(file_path, file.filename or "unknown")

        # Step 3: Normalize into structured format
        normalized = structured_parser.parse_resume(
            text=parsed.full_text,
            filename=file.filename or "unknown",
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Resume normalized successfully",
                "data": {
                    "upload": upload_data,
                    "normalized": normalized.model_dump(),
                },
            },
        )

    except FileValidationError as e:
        return JSONResponse(status_code=e.status_code, content=e.to_dict())

    except ParseError as e:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": f"Parsing failed: {e.message}",
                "errors": None,
            },
        )

    except Exception as e:
        logger.exception("Normalize error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "errors": None,
            },
        )


@router.post("/extract")
async def extract_entities(
    file: UploadFile = File(...),
) -> JSONResponse:
    """Parse, normalize, and extract entities from a resume.

    Full pipeline: upload → parse → normalize → extract.
    Returns extracted entities (emails, phones, skills, dates, etc.).

    Args:
        file: The resume file to extract from (PDF or DOCX).

    Returns:
        JSONResponse: Extracted entities and skills.
    """
    upload_service = UploadService()
    parser = ResumeParser()
    structured_parser = StructuredParser()
    extraction_engine = ExtractionEngine()

    try:
        # Step 1: Upload and store
        upload_result = await upload_service.upload_resume(file)
        upload_data = upload_result["data"]
        upload_data["upload_timestamp"] = upload_data["upload_timestamp"].isoformat()
        stored_filename = upload_data["stored_filename"]

        # Step 2: Parse the stored file
        file_path = f"uploads/resumes/{stored_filename}"
        parsed = parser.parse(file_path, file.filename or "unknown")

        # Step 3: Normalize into structured format
        normalized = structured_parser.parse_resume(
            text=parsed.full_text,
            filename=file.filename or "unknown",
        )

        # Step 4: Extract entities and skills
        extraction_result = extraction_engine.extract(
            text=parsed.full_text,
            filename=file.filename or "unknown",
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Extraction completed successfully",
                "data": {
                    "upload": upload_data,
                    "normalized": normalized.model_dump(),
                    "extraction": extraction_result.model_dump(),
                },
            },
        )

    except FileValidationError as e:
        return JSONResponse(status_code=e.status_code, content=e.to_dict())

    except ParseError as e:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": f"Parsing failed: {e.message}",
                "errors": None,
            },
        )

    except Exception as e:
        logger.exception("Extraction error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "errors": None,
            },
        )


@router.post("/validate")
async def validate_resume(
    file: UploadFile = File(...),
) -> JSONResponse:
    """Parse, normalize, and validate a resume against ATS rules.

    Full pipeline: upload → parse → normalize → rule engine.
    Returns scores, grades, and actionable feedback.

    Args:
        file: The resume file to validate (PDF or DOCX).

    Returns:
        JSONResponse: Validation results with scores and issues.
    """
    upload_service = UploadService()
    parser = ResumeParser()
    structured_parser = StructuredParser()
    rule_engine = RuleEngine()

    try:
        # Step 1: Upload and store
        upload_result = await upload_service.upload_resume(file)
        upload_data = upload_result["data"]
        upload_data["upload_timestamp"] = upload_data["upload_timestamp"].isoformat()
        stored_filename = upload_data["stored_filename"]

        # Step 2: Parse the stored file
        file_path = f"uploads/resumes/{stored_filename}"
        parsed = parser.parse(file_path, file.filename or "unknown")

        # Step 3: Normalize into structured format
        normalized = structured_parser.parse_resume(
            text=parsed.full_text,
            filename=file.filename or "unknown",
        )

        # Step 4: Run rule engine
        rule_result = rule_engine.evaluate(normalized)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Validation completed successfully",
                "data": {
                    "upload": upload_data,
                    "normalized": normalized.model_dump(),
                    "validation": rule_result.model_dump(),
                },
            },
        )

    except FileValidationError as e:
        return JSONResponse(status_code=e.status_code, content=e.to_dict())

    except ParseError as e:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": f"Parsing failed: {e.message}",
                "errors": None,
            },
        )

    except Exception as e:
        logger.exception("Validation error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "errors": None,
            },
        )
