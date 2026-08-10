"""Unit tests for Multi-ATS emulation engine."""

from backend.ats.engine import MultiATSEmulator
from backend.schemas.resume import ContactInfo, Experience, NormalizedResume, ResumeSection, SkillCategory


def test_multi_ats_emulator_all_pass():
    emulator = MultiATSEmulator()

    resume = NormalizedResume(
        filename="resume.pdf",
        contact=ContactInfo(name="John Doe", email="john@example.com", phone="1234567890", linkedin="https://linkedin.com/in/johndoe"),
        sections_detected=[
            ResumeSection(section_type="experience", title="Work Experience"),
            ResumeSection(section_type="education", title="Education"),
            ResumeSection(section_type="skills", title="Skills"),
        ],
        experience=[
            Experience(
                title="Senior Software Engineer",
                company="Tech Corp",
                location="San Francisco, CA",
                bullets=[
                    "Engineered distributed backend microservices handling 50k requests/sec using Python and FastAPI.",
                    "Spearheaded cloud migration to AWS reducing hosting costs by 35%.",
                ],
            )
        ],
        skills=[SkillCategory(category="Technical", skills=["Python", "FastAPI"])],
        education=[],
    )

    result = emulator.evaluate_all(resume)

    assert result.average_score > 70
    assert result.workday.status in ["Pass", "Warning"]
    assert result.greenhouse.status in ["Pass", "Warning"]
    assert result.lever.status == "Pass"
    assert result.taleo.status in ["Pass", "Warning"]
    assert result.icims.status in ["Pass", "Warning"]
