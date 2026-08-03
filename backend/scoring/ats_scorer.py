"""ATS scorer — coordinates all scoring components.

This module combines all scoring components into a final ATS score
with complete breakdown and explanations.

Formula:
ATS Score = 35% Skills + 25% Experience + 15% Projects
          + 10% Education + 10% Structure + 5% Formatting
"""

import time

from backend.scoring.skills_scorer import score_skills
from backend.scoring.experience_scorer import score_experience
from backend.schemas.jd import JobDescription
from backend.schemas.resume import NormalizedResume
from backend.schemas.scoring import ATSScore, ScoreBreakdown, ScoreDetail
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ATSScorer:
    """Calculate ATS score for resume-JD match."""

    def score(self, resume: NormalizedResume, jd: JobDescription) -> ATSScore:
        """Calculate complete ATS score.

        Args:
            resume: Parsed resume.
            jd: Parsed job description.

        Returns:
            ATSScore with breakdown and explanations.
        """
        start = time.time()

        # Score each category
        skills_score = score_skills(resume, jd)
        experience_score = score_experience(resume, jd)
        projects_score = self._score_projects(resume, jd)
        education_score = self._score_education(resume, jd)
        structure_score = self._score_structure(resume)
        formatting_score = self._score_formatting(resume)

        # Create breakdown
        breakdown = ScoreBreakdown(
            skills=skills_score,
            experience=experience_score,
            projects=projects_score,
            education=education_score,
            structure=structure_score,
            formatting=formatting_score,
        )

        # Calculate overall score
        overall_score = (
            skills_score.weighted_score
            + experience_score.weighted_score
            + projects_score.weighted_score
            + education_score.weighted_score
            + structure_score.weighted_score
            + formatting_score.weighted_score
        )

        # Calculate deductions
        total_deductions = (
            (100 - skills_score.score) * 0.35
            + (100 - experience_score.score) * 0.25
            + (100 - projects_score.score) * 0.15
            + (100 - education_score.score) * 0.10
            + (100 - structure_score.score) * 0.10
            + (100 - formatting_score.score) * 0.05
        )

        # Get missing skills
        missing_skills = self._get_missing_skills(resume, jd)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            skills_score, experience_score, missing_skills
        )

        grade = self._calculate_grade(overall_score)

        elapsed = (time.time() - start) * 1000

        logger.info(
            "ATS Score: %.0f/100 (Grade: %s) in %.2f ms",
            overall_score, grade, elapsed,
        )

        return ATSScore(
            resume_filename=resume.filename,
            jd_title=jd.title,
            overall_score=overall_score,
            overall_grade=grade,
            breakdown=breakdown,
            total_deductions=total_deductions,
            missing_skills=missing_skills,
            recommendations=recommendations,
            scoring_time_ms=round(elapsed, 2),
        )

    def _score_projects(self, resume: NormalizedResume, jd: JobDescription) -> ScoreDetail:
        """Score projects relevance."""
        reasoning = []
        score = 0.0

        if not resume.projects:
            reasoning.append("No projects listed in resume")
            return ScoreDetail(
                category="projects",
                score=0,
                max_score=100,
                weight=0.15,
                weighted_score=0,
                reasoning=reasoning,
                passed=False,
            )

        # Simple heuristic: more projects = higher score
        num_projects = len(resume.projects)
        if num_projects >= 3:
            score = 80
            reasoning.append(f"✓ Good number of projects: {num_projects}")
        elif num_projects >= 1:
            score = 50
            reasoning.append(f"✓ Has {num_projects} project(s)")
        else:
            score = 0
            reasoning.append("✗ No projects listed")

        # Check for relevant keywords in project descriptions
        jd_text = jd.description.lower()
        relevant_projects = 0
        for proj in resume.projects:
            proj_text = (proj.name + " " + proj.description).lower()
            # Check if any JD keywords appear in project
            if any(kw in proj_text for kw in jd_text.split()[:50]):
                relevant_projects += 1

        if relevant_projects > 0:
            score = min(100, score + relevant_projects * 10)
            reasoning.append(f"✓ {relevant_projects} project(s) relevant to JD")

        return ScoreDetail(
            category="projects",
            score=min(100, score),
            max_score=100,
            weight=0.15,
            weighted_score=min(100, score) * 0.15,
            reasoning=reasoning,
            passed=score >= 50,
        )

    def _score_education(self, resume: NormalizedResume, jd: JobDescription) -> ScoreDetail:
        """Score education match."""
        reasoning = []
        score = 50  # Default: neutral

        if resume.education:
            score = 80
            reasoning.append(f"✓ Has {len(resume.education)} education entry/entries")
        else:
            score = 20
            reasoning.append("✗ No education listed")

        # Check if JD specifies education requirements
        if jd.education:
            required_fields = [e.field.lower() for e in jd.education if e.required]
            if required_fields:
                resume_fields = [e.field.lower() for e in resume.education]
                matched = any(f in " ".join(resume_fields) for f in required_fields)
                if matched:
                    score = 100
                    reasoning.append("✓ Education field matches JD requirement")
                else:
                    score = max(30, score - 30)
                    reasoning.append("✗ Education field may not match JD requirement")

        return ScoreDetail(
            category="education",
            score=score,
            max_score=100,
            weight=0.10,
            weighted_score=score * 0.10,
            reasoning=reasoning,
            passed=score >= 50,
        )

    def _score_structure(self, resume: NormalizedResume) -> ScoreDetail:
        """Score resume structure completeness."""
        reasoning = []
        score = 0.0

        sections = {
            "contact": bool(resume.contact and resume.contact.email),
            "summary": bool(resume.summary),
            "experience": bool(resume.experience),
            "skills": bool(resume.skills),
            "education": bool(resume.education),
        }

        present = sum(1 for v in sections.values() if v)
        total = len(sections)

        for name, exists in sections.items():
            if exists:
                reasoning.append(f"✓ Has {name} section")
            else:
                reasoning.append(f"✗ Missing {name} section")

        score = (present / total) * 100

        return ScoreDetail(
            category="structure",
            score=score,
            max_score=100,
            weight=0.10,
            weighted_score=score * 0.10,
            reasoning=reasoning,
            passed=present >= 4,
        )

    def _score_formatting(self, resume: NormalizedResume) -> ScoreDetail:
        """Score formatting quality."""
        reasoning = []
        score = 70  # Default good score

        # Check bullet lengths
        all_bullets = []
        for exp in resume.experience:
            all_bullets.extend(exp.bullets)

        if all_bullets:
            avg_length = sum(len(b) for b in all_bullets) / len(all_bullets)
            if 40 <= avg_length <= 200:
                reasoning.append("✓ Good bullet point length")
            elif avg_length < 40:
                score -= 20
                reasoning.append("✗ Some bullets too short")
            else:
                score -= 10
                reasoning.append("✗ Some bullets too long")
        else:
            reasoning.append("No bullets to evaluate")

        return ScoreDetail(
            category="formatting",
            score=max(0, score),
            max_score=100,
            weight=0.05,
            weighted_score=max(0, score) * 0.05,
            reasoning=reasoning,
            passed=score >= 50,
        )

    def _get_missing_skills(self, resume: NormalizedResume, jd: JobDescription) -> list[str]:
        """Get skills required by JD but missing from resume."""
        resume_skills = set()
        for cat in resume.skills:
            for skill in cat.skills:
                resume_skills.add(skill.lower())

        missing = []
        for jd_skill in jd.skills:
            if jd_skill.required and jd_skill.name.lower() not in resume_skills:
                missing.append(jd_skill.name)

        return missing

    def _generate_recommendations(
        self,
        skills: ScoreDetail,
        experience: ScoreDetail,
        missing_skills: list[str],
    ) -> list[str]:
        """Generate improvement recommendations."""
        recs = []

        if not skills.passed:
            recs.append("Add more relevant skills from the job description")

        if missing_skills:
            recs.append(f"Consider adding these skills: {', '.join(missing_skills[:5])}")

        if not experience.passed:
            recs.append("Highlight more relevant work experience")

        if not recs:
            recs.append("Your resume looks good! Consider minor optimizations.")

        return recs

    def _calculate_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
