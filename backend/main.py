from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes.jd import router as jd_router
from backend.api.routes.metrics import router as metrics_router
from backend.api.routes.resume import router as resume_router
from backend.api.routes.rewrite import router as rewrite_router
from backend.api.routes.score import router as score_router
from backend.api.routes.search import router as search_router
from backend.config.settings import settings
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager for startup/shutdown events."""
    setup_logging()
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)

app.include_router(resume_router)
app.include_router(jd_router)
app.include_router(search_router)
app.include_router(score_router)
app.include_router(rewrite_router)
app.include_router(metrics_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
