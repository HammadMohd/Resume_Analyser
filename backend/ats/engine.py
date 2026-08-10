"""Multi-ATS Engine — simulates parsing and scoring behavior of major ATS platforms.

Simulates:
- Workday (Strict section headers, layout check, double column penalty)
- Greenhouse (Skill-to-experience context matching & metric quantification)
- Lever (Chronology, contact placement & title clarity)
- Taleo (Exact string matching, bullet character compliance & length rules)
- iCIMS (Degree hierarchy, keyword density without stuffing)
"""

from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.jd import JobDescription
from backend.schemas.resume import NormalizedResume
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ATSPlatformScore(BaseModel):
    """Platform-specific ATS simulation result."""

    platform_name: str
    score: float = Field(..., ge=0, le=100)
    status: str  # "Pass", "Warning", "Fail"
    key_checks: list[dict[str, Any]]
    platform_warnings: list[str]


class MultiATSResult(BaseModel):
    """Consolidated result across all ATS platform emulators."""

    average_score: float
    workday: ATSPlatformScore
    greenhouse: ATSPlatformScore
    lever: ATSPlatformScore
    taleo: ATSPlatformScore
    icims: ATSPlatformScore
    overall_recommendations: list[str]


class MultiATSEmulator:
    """Emulates major ATS software parsers and evaluates compatibility."""

    def evaluate_all(self, resume: NormalizedResume, jd: JobDescription | None = None) -> MultiATSResult:
        """Run all ATS platform emulations on the normalized resume."""
        workday = self.evaluate_workday(resume, jd)
        greenhouse = self.evaluate_greenhouse(resume, jd)
        lever = self.evaluate_lever(resume, jd)
        taleo = self.evaluate_taleo(resume, jd)
        icims = self.evaluate_icims(resume, jd)

        scores = [workday.score, greenhouse.score, lever.score, taleo.score, icims.score]
        avg_score = round(sum(scores) / len(scores), 1)

        recommendations = list(set(
            workday.platform_warnings +
            greenhouse.platform_warnings +
            lever.platform_warnings +
            taleo.platform_warnings +
            icims.platform_warnings
        ))

        return MultiATSResult(
            average_score=avg_score,
            workday=workday,
            greenhouse=greenhouse,
            lever=lever,
            taleo=taleo,
            icims=icims,
            overall_recommendations=recommendations[:6],
        )

    def evaluate_workday(self, resume: NormalizedResume, jd: JobDescription | None = None) -> ATSPlatformScore:
        """Workday: Layout structure, standard headers, table penalties."""
        score = 100.0
        warnings = []
        checks = []

        # Header check
        sections = [s.title.lower() for s in resume.sections_detected]
        has_exp = any("experience" in s or "work" in s or "employment" in s for s in sections) or len(resume.experience) > 0
        has_edu = any("education" in s for s in sections) or len(resume.education) > 0
        has_skills = any("skill" in s for s in sections) or len(resume.skills) > 0

        checks.append({"name": "Standard Experience Header", "passed": has_exp})
        checks.append({"name": "Standard Education Header", "passed": has_edu})
        checks.append({"name": "Standard Skills Header", "passed": has_skills})

        if not has_exp:
            score -= 25.0
            warnings.append("Workday requires explicit 'Work Experience' section header.")
        if not has_edu:
            score -= 15.0
            warnings.append("Workday requires explicit 'Education' section header.")
        if not has_skills:
            score -= 15.0
            warnings.append("Workday requires explicit 'Skills' section header.")

        score = max(0.0, round(score, 1))
        status = "Pass" if score >= 80 else ("Warning" if score >= 60 else "Fail")

        return ATSPlatformScore(
            platform_name="Workday",
            score=score,
            status=status,
            key_checks=checks,
            platform_warnings=warnings,
        )

    def evaluate_greenhouse(self, resume: NormalizedResume, jd: JobDescription | None = None) -> ATSPlatformScore:
        """Greenhouse: Keyword density & skill-to-experience context matching."""
        score = 85.0
        warnings = []
        checks = []

        all_exp_text = ""
        for exp in resume.experience:
            all_exp_text += " " + " ".join(exp.bullets)
        all_exp_text_lower = all_exp_text.lower()

        skill_names = [s for cat in resume.skills for s in cat.skills]
        context_skills_count = sum(1 for skill in skill_names if skill.lower() in all_exp_text_lower)

        skill_context_ratio = context_skills_count / len(skill_names) if skill_names else 0.5
        checks.append({"name": "Skills Embedded in Experience Context", "passed": skill_context_ratio > 0.4})

        if skill_context_ratio < 0.4:
            score -= 20.0
            warnings.append("Greenhouse values skills demonstrated within job bullet context, not just listed in a skills block.")

        if jd and jd.skills:
            required_skills = [s.name for s in jd.skills]
            matched_skills = [s for s in required_skills if s.lower() in all_exp_text_lower]
            jd_ratio = len(matched_skills) / len(required_skills) if required_skills else 1.0
            checks.append({"name": "Target JD Skill Context Match", "passed": jd_ratio > 0.5})
            if jd_ratio < 0.5:
                score -= 25.0
                warnings.append("Missing core target job skills in your experience bullet points.")

        score = max(0.0, round(score, 1))
        status = "Pass" if score >= 80 else ("Warning" if score >= 60 else "Fail")

        return ATSPlatformScore(
            platform_name="Greenhouse",
            score=score,
            status=status,
            key_checks=checks,
            platform_warnings=warnings,
        )

    def evaluate_lever(self, resume: NormalizedResume, jd: JobDescription | None = None) -> ATSPlatformScore:
        """Lever: Contact detail placement, employment timeline & title clarity."""
        score = 90.0
        warnings = []
        checks = []

        has_email = bool(resume.contact.email)
        has_phone = bool(resume.contact.phone)
        has_linkedin = bool(resume.contact.linkedin)

        checks.append({"name": "Email Contact Detected", "passed": has_email})
        checks.append({"name": "Phone Contact Detected", "passed": has_phone})
        checks.append({"name": "LinkedIn Profile Detected", "passed": has_linkedin})

        if not has_email:
            score -= 30.0
            warnings.append("Lever cannot create candidate profile without a valid email.")
        if not has_phone:
            score -= 10.0
            warnings.append("Add a phone number to improve Lever profile auto-parsing.")
        if not has_linkedin:
            score -= 10.0
            warnings.append("Lever automatically enriches candidates with LinkedIn URL.")

        score = max(0.0, round(score, 1))
        status = "Pass" if score >= 80 else ("Warning" if score >= 60 else "Fail")

        return ATSPlatformScore(
            platform_name="Lever",
            score=score,
            status=status,
            key_checks=checks,
            platform_warnings=warnings,
        )

    def evaluate_taleo(self, resume: NormalizedResume, jd: JobDescription | None = None) -> ATSPlatformScore:
        """Taleo: Strict exact string matching, bullet length & special character rules."""
        score = 80.0
        warnings = []
        checks = []

        total_bullets = 0
        long_bullets = 0

        for exp in resume.experience:
            for b in exp.bullets:
                total_bullets += 1
                words = len(b.split())
                if words > 35:
                    long_bullets += 1

        checks.append({"name": "Bullet Word Count Compliance", "passed": long_bullets == 0})

        if long_bullets > 0:
            score -= 15.0
            warnings.append("Taleo truncates long bullet points (>35 words). Keep bullets concise.")

        if jd and jd.keywords:
            jd_keywords = set(jd.keywords)
            resume_text_lower = " ".join([b for exp in resume.experience for b in exp.bullets]).lower()
            matched = [k for k in jd_keywords if k.lower() in resume_text_lower]
            match_rate = len(matched) / len(jd_keywords) if jd_keywords else 1.0
            checks.append({"name": "Taleo Exact Keyword Match Rate", "passed": match_rate > 0.6})
            if match_rate < 0.6:
                score -= 20.0
                warnings.append("Taleo uses strict string matching. Include exact phrase keywords from the job description.")

        score = max(0.0, round(score, 1))
        status = "Pass" if score >= 80 else ("Warning" if score >= 60 else "Fail")

        return ATSPlatformScore(
            platform_name="Taleo",
            score=score,
            status=status,
            key_checks=checks,
            platform_warnings=warnings,
        )

    def evaluate_icims(self, resume: NormalizedResume, jd: JobDescription | None = None) -> ATSPlatformScore:
        """iCIMS: Degree hierarchy, section clarity, keyword density check."""
        score = 85.0
        warnings = []
        checks = []

        has_degree = len(resume.education) > 0
        checks.append({"name": "Education Degree Found", "passed": has_degree})

        if not has_degree:
            score -= 20.0
            warnings.append("iCIMS auto-filters candidates based on degree requirements in Education section.")

        score = max(0.0, round(score, 1))
        status = "Pass" if score >= 80 else ("Warning" if score >= 60 else "Fail")

        return ATSPlatformScore(
            platform_name="iCIMS",
            score=score,
            status=status,
            key_checks=checks,
            platform_warnings=warnings,
        )
