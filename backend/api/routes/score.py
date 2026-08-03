"""Scoring router — HTTP layer for ATS scoring endpoints.

This router owns all scoring-related endpoints under /api/v1/score.
"""

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from backend.jd.jd_parser import JDParser
from backend.parser.resume_parser import ResumeParser
from backend.parser.structured_parser import StructuredParser
from backend.scoring.ats_scorer import ATSScorer
from backend.services.upload_service import UploadService
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/score", tags=["scoring"])


@router.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...),
) -> JSONResponse:
    """Analyze resume against job description and calculate ATS score.

    Upload both files and get a comprehensive ATS score with
    breakdown, explanations, and recommendations.

    Args:
        resume: Resume file (PDF or DOCX).
        jd: Job description file (TXT, PDF, or DOCX).

    Returns:
        JSONResponse: ATS score with breakdown and recommendations.
    """
    upload_service = UploadService()
    parser = ResumeParser()
    structured_parser = StructuredParser()
    jd_parser = JDParser()
    scorer = ATSScorer()

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

        # If PDF/DOCX, parse it
        if jd.filename and (jd.filename.endswith(".pdf") or jd.filename.endswith(".docx")):
            import os
            import tempfile

            suffix = ".pdf" if jd.filename.endswith(".pdf") else ".docx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(jd_content)
                tmp_path = tmp.name

            try:
                parsed_jd_file = parser.parse(tmp_path, jd.filename)
                jd_text = parsed_jd_file.full_text
            finally:
                os.unlink(tmp_path)

        jd_result = jd_parser.parse(jd_text, title=jd.filename or "")

        # Score
        ats_score = scorer.score(normalized_resume, jd_result)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "ATS scoring completed successfully",
                "data": ats_score.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("Scoring error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Scoring error: {str(e)}",
                "errors": None,
            },
        )


@router.post("/analyze-text")
async def analyze_text(
    resume_text: str = Form(...),
    jd_text: str = Form(...),
) -> JSONResponse:
    """Analyze raw resume text against raw JD text.

    For quick testing without file uploads.

    Args:
        resume_text: Raw resume text.
        jd_text: Raw job description text.

    Returns:
        JSONResponse: ATS score with breakdown.
    """
    structured_parser = StructuredParser()
    jd_parser = JDParser()
    scorer = ATSScorer()

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

        # Score
        ats_score = scorer.score(normalized_resume, parsed_jd)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "ATS scoring completed successfully",
                "data": ats_score.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("Scoring error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Scoring error: {str(e)}",
                "errors": None,
            },
        )
