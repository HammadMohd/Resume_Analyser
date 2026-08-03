"""Search router — HTTP layer for search/matching endpoints.

This router owns all search-related endpoints under /api/v1/search.
"""

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from backend.jd.jd_parser import JDParser
from backend.parser.resume_parser import ResumeParser
from backend.parser.structured_parser import StructuredParser
from backend.search.hybrid_search import HybridSearch
from backend.services.upload_service import UploadService
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.post("/match")
async def match_resume_to_jd(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...),
) -> JSONResponse:
    """Match a resume against a job description.

    Upload both files and get a comprehensive match analysis
    including BM25 score, embedding similarity, and skill matches.

    Args:
        resume: Resume file (PDF or DOCX).
        jd: Job description file (TXT, PDF, or DOCX).

    Returns:
        JSONResponse: Match result with scores and skill analysis.
    """
    upload_service = UploadService()
    parser = ResumeParser()
    structured_parser = StructuredParser()
    jd_parser = JDParser()
    search = HybridSearch()

    try:
        # Parse resume
        resume_result = await upload_service.upload_resume(resume)
        stored_filename = resume_result["data"]["stored_filename"]
        file_path = f"uploads/resumes/{stored_filename}"
        parsed_resume = parser.parse(file_path, resume.filename or "unknown")
        normalized_resume = structured_parser.parse_resume(
            text=parsed_resume.raw_text,
            filename=resume.filename or "unknown",
        )

        # Parse JD
        jd_content = await jd.read()
        jd_text = jd_content.decode("utf-8", errors="ignore")

        # If PDF/DOCX, parse it
        if jd.filename and (jd.filename.endswith(".pdf") or jd.filename.endswith(".docx")):
            import tempfile
            import os

            suffix = ".pdf" if jd.filename.endswith(".pdf") else ".docx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(jd_content)
                tmp_path = tmp.name

            try:
                parsed_jd = parser.parse(tmp_path, jd.filename)
                jd_text = parsed_jd.raw_text
            finally:
                os.unlink(tmp_path)

        parsed_jd = jd_parser.parse(jd_text, title=jd.filename or "")

        # Match
        match_result = search.match(normalized_resume, parsed_jd)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Match completed successfully",
                "data": match_result.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("Match error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Match error: {str(e)}",
                "errors": None,
            },
        )


@router.post("/match-text")
async def match_text_to_jd(
    resume_text: str = Form(...),
    jd_text: str = Form(...),
) -> JSONResponse:
    """Match raw resume text against raw JD text.

    For quick testing without file uploads.

    Args:
        resume_text: Raw resume text.
        jd_text: Raw job description text.

    Returns:
        JSONResponse: Match result with scores.
    """
    structured_parser = StructuredParser()
    jd_parser = JDParser()
    search = HybridSearch()

    try:
        if not resume_text or not jd_text:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": "Both resume_text and jd_text are required",
                    "errors": None,
                },
            )

        # Parse both
        normalized_resume = structured_parser.parse_resume(
            text=resume_text,
            filename="input",
        )
        parsed_jd = jd_parser.parse(jd_text, title="Input JD")

        # Match
        match_result = search.match(normalized_resume, parsed_jd)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Match completed successfully",
                "data": match_result.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("Match error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Match error: {str(e)}",
                "errors": None,
            },
        )
