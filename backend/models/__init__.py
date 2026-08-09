"""Database models initialization."""

from backend.db.base import Base
from backend.models.analysis import AnalysisModel
from backend.models.job_description import JobDescriptionModel
from backend.models.resume import ResumeModel
from backend.models.tailored_resume import TailoredResumeModel

__all__ = ["Base", "ResumeModel", "JobDescriptionModel", "AnalysisModel", "TailoredResumeModel"]
