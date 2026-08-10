"""Unit tests for Impact Analysis and AI STAR Tailoring."""

from backend.llm.star_rewriter import STARBulletEnhancer
from backend.schemas.jd import JDSkill, JobDescription
from backend.schemas.resume import ContactInfo, Experience, NormalizedResume, SkillCategory
from backend.scoring.impact_analyzer import ImpactAnalyzer
from backend.services.tailor_service import ResumeTailorService


def test_impact_analyzer():
    analyzer = ImpactAnalyzer()
    resume = NormalizedResume(
        filename="resume.pdf",
        contact=ContactInfo(name="Jane Doe"),
        experience=[
            Experience(
                title="Developer",
                bullets=[
                    "Engineered cloud infrastructure reducing latency by 45%.",
                    "Worked on team project.",
                ],
            )
        ],
    )

    res = analyzer.analyze(resume)
    assert res.total_bullets_count == 2
    assert res.quantified_bullets_count == 1
    assert res.quantified_bullet_ratio == 0.5


def test_star_enhancer():
    enhancer = STARBulletEnhancer()
    res = enhancer.enhance_bullet("worked on database optimization", target_skill="PostgreSQL")
    assert res.original_bullet == "worked on database optimization"
    assert "PostgreSQL" in res.star_bullet


def test_tailor_service():
    service = ResumeTailorService()
    resume = NormalizedResume(
        filename="resume.pdf",
        contact=ContactInfo(name="Jane"),
        experience=[Experience(title="Engineer", bullets=["Built web applications."])],
        skills=[SkillCategory(category="Technical", skills=["Python"])],
    )
    jd = JobDescription(
        title="Backend Engineer",
        skills=[JDSkill(name="FastAPI"), JDSkill(name="Docker"), JDSkill(name="Redis")],
    )

    res = service.tailor_resume(resume, jd)
    assert res.target_job_title == "Backend Engineer"
    assert len(res.tailored_bullets) > 0
