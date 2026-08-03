"""Job Description router — HTTP layer for JD endpoints.

This router owns all JD-related endpoints under /api/v1/jd.
"""

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from backend.jd.jd_parser import JDParser
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/jd", tags=["job-descriptions"])


@router.post("/parse")
async def parse_job_description(
    file: UploadFile = File(...),
) -> JSONResponse:
    """Parse a job description file (TXT, DOCX, or PDF).

    Extracts skills, experience, education, and keywords from the JD.

    Args:
        file: The job description file to parse.

    Returns:
        JSONResponse: Parsed job description data.
    """
    from backend.parser.resume_parser import ResumeParser

    parser = ResumeParser()
    jd_parser = JDParser()

    try:
        # Read file content
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")

        # If it's a PDF/DOCX, parse it first
        if file.filename and (file.filename.endswith(".pdf") or file.filename.endswith(".docx")):
            import os
            import tempfile

            # Save to temp file
            suffix = ".pdf" if file.filename.endswith(".pdf") else ".docx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                parsed = parser.parse(tmp_path, file.filename)
                text = parsed.full_text
            finally:
                os.unlink(tmp_path)

        # Parse JD
        jd = jd_parser.parse(text, title=file.filename or "")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Job description parsed successfully",
                "data": jd.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("JD parse error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Parse error: {str(e)}",
                "errors": None,
            },
        )


@router.post("/parse-text")
async def parse_job_description_text(
    text: str = Form(...),
    title: str = Form(default=""),
) -> JSONResponse:
    """Parse job description from raw text input.

    Accepts plain text JD content and returns structured data.

    Args:
        text: Raw job description text.
        title: Optional job title.

    Returns:
        JSONResponse: Parsed job description data.
    """
    jd_parser = JDParser()

    try:
        if not text:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": "No text provided",
                    "errors": None,
                },
            )

        jd = jd_parser.parse(text, title=title)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Job description parsed successfully",
                "data": jd.model_dump(),
            },
        )

    except Exception as e:
        logger.exception("JD parse error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Parse error: {str(e)}",
                "errors": None,
            },
        )
