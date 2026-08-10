"""Unit tests for PDF and DOCX Resume Exporters."""

from backend.exporter.docx_generator import DOCXResumeExporter
from backend.exporter.pdf_generator import PDFResumeExporter
from backend.schemas.resume import ContactInfo, Education, Experience, NormalizedResume, SkillCategory


def test_pdf_exporter():
    exporter = PDFResumeExporter()
    resume = NormalizedResume(
        filename="test.pdf",
        contact=ContactInfo(name="John Doe", email="john@example.com", phone="1234567890"),
        experience=[
            Experience(
                title="Senior Developer",
                company="TechCorp",
                start_date="2020",
                end_date="Present",
                bullets=["Built microservices with FastAPI and Python."],
            )
        ],
        education=[Education(degree="BS Computer Science", institution="University X", start_date="2016", end_date="2020")],
        skills=[SkillCategory(category="Languages", skills=["Python", "SQL"])],
    )

    pdf_bytes = exporter.export_pdf(resume)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_docx_exporter():
    exporter = DOCXResumeExporter()
    resume = NormalizedResume(
        filename="test.docx",
        contact=ContactInfo(name="Jane Doe", email="jane@example.com"),
        experience=[
            Experience(
                title="Lead Architect",
                company="Innovate",
                start_date="2021",
                end_date="Present",
                bullets=["Orchestrated cloud deployments."],
            )
        ],
        education=[Education(degree="MS Data Science", institution="Tech Institute")],
        skills=[SkillCategory(category="Cloud", skills=["AWS", "Docker"])],
    )

    docx_bytes = exporter.export_docx(resume)
    assert len(docx_bytes) > 0
