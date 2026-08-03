"""Rewrite router — HTTP layer for bullet rewriting endpoints.

This router owns all rewrite-related endpoints under /api/v1/rewrite.
"""

from fastapi import APIRouter
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
