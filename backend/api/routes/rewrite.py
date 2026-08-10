"""Rewrite router — HTTP layer for bullet rewriting endpoints.

This router owns all rewrite-related endpoints under /api/v1/rewrite.
"""

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from backend.llm.rewriter import BulletRewriter
from backend.llm.schemas import BulletRewriteRequest, RewriteRequest
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/rewrite", tags=["rewrite"])


@router.post("/bullet")
async def rewrite_single_bullet(
    original: str = "",
    context: str = "",
) -> JSONResponse:
    """Rewrite a single bullet point.

    Args:
        original: Original bullet text.
        context: Job title or context.

    Returns:
        JSONResponse: Rewritten bullet with metadata.
    """
    rewriter = BulletRewriter()

    try:
        if not original:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": "Original bullet text is required",
                    "errors": None,
                },
            )

        request = BulletRewriteRequest(original=original, context=context)
        result = rewriter.rewrite_bullet(request)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Bullet rewritten successfully",
                "data": result.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("Rewrite error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Rewrite error: {str(e)}",
                "errors": None,
            },
        )


@router.post("/bullets")
async def rewrite_multiple_bullets(
    request: RewriteRequest,
) -> JSONResponse:
    """Rewrite multiple bullet points.

    Args:
        request: Rewrite request with bullets to improve.

    Returns:
        JSONResponse: All rewritten bullets with metadata.
    """
    rewriter = BulletRewriter()

    try:
        if not request.bullets:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": "No bullets provided",
                    "errors": None,
                },
            )

        result = rewriter.rewrite_bullets(request)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Bullets rewritten successfully",
                "data": result.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("Rewrite error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Rewrite error: {str(e)}",
                "errors": None,
            },
        )


@router.post("/validate")
async def validate_bullet(
    original: str = "",
    improved: str = "",
) -> JSONResponse:
    """Validate an improved bullet point.

    Args:
        original: Original bullet text.
        improved: Improved bullet text.

    Returns:
        JSONResponse: Validation result.
    """
    from backend.llm.validator import validate_bullet_rewrite

    try:
        if not original or not improved:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": "Both original and improved text required",
                    "errors": None,
                },
            )

        result = validate_bullet_rewrite(original, improved)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Validation completed",
                "data": result.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("Validation error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Validation error: {str(e)}",
                "errors": None,
            },
        )


@router.post("/tailor")
async def tailor_resume_to_jd(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...),
) -> JSONResponse:
    """Tailor experience bullet points to match a target job description using STAR framework."""
    from backend.jd.jd_parser import JDParser
    from backend.parser.resume_parser import ResumeParser
    from backend.parser.structured_parser import StructuredParser
    from backend.services.tailor_service import ResumeTailorService
    from backend.services.upload_service import UploadService

    upload_service = UploadService()
    parser = ResumeParser()
    structured_parser = StructuredParser()
    jd_parser = JDParser()
    tailor_service = ResumeTailorService()

    try:
        # Parse resume
        resume_result = await upload_service.upload_resume(resume)
        stored_filename = resume_result["data"]["stored_filename"]
        file_path = f"uploads/resumes/{stored_filename}"
        parsed_resume = parser.parse(file_path, resume.filename or "unknown")
        normalized_resume = structured_parser.parse_resume(
            text=parsed_resume.full_text,
            filename=resume.filename or "unknown",
        )

        # Parse JD
        jd_content = await jd.read()
        jd_text = jd_content.decode("utf-8", errors="ignore")
        parsed_jd = jd_parser.parse(jd_text, title=jd.filename or "")

        tailored_response = tailor_service.tailor_resume(normalized_resume, parsed_jd)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Resume tailored successfully",
                "data": tailored_response.model_dump(),
            },
        )
    except Exception as e:
        logger.exception("Tailoring error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Tailor error: {str(e)}", "errors": None},
        )

