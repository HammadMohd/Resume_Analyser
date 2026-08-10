"""ATS-Compliant PDF Resume Exporter using ReportLab.

Generates single-column, clean, ATS-proof PDF resume documents.
"""

import io

from backend.schemas.resume import NormalizedResume
from backend.utils.logging import get_logger

logger = get_logger(__name__)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.info("ReportLab not available for PDF export.")


class PDFResumeExporter:
    """Exports structured resume into an ATS-tested, clean PDF layout."""

    def export_pdf(self, resume: NormalizedResume) -> bytes:
        """Generate PDF bytes for the given normalized resume."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab library is required for PDF generation.")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        styles = getSampleStyleSheet()
        story = []

        # Name / Header Style
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            spaceAfter=4,
            textColor="#1e293b",
        )
        subtitle_style = ParagraphStyle(
            "SubTitleStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            spaceAfter=12,
            textColor="#475569",
        )
        section_style = ParagraphStyle(
            "SectionStyle",
            parent=styles["Heading2"],
            fontSize=12,
            leading=14,
            spaceBefore=10,
            spaceAfter=4,
            textColor="#0f172a",
        )
        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            spaceAfter=3,
            textColor="#334155",
        )

        # Header Contact
        contact_str = f"{resume.contact.email or ''} | {resume.contact.phone or ''} | {resume.contact.location or ''}"
        story.append(Paragraph(resume.contact.name or "Candidate Resume", title_style))
        story.append(Paragraph(contact_str, subtitle_style))
        story.append(Spacer(1, 6))

        # Experience
        if resume.experience:
            story.append(Paragraph("WORK EXPERIENCE", section_style))
            for exp in resume.experience:
                date_str = f"{exp.start_date} - {exp.end_date}".strip(" -") if (exp.start_date or exp.end_date) else ""
                role_header = f"<b>{exp.title}</b> &mdash; <i>{exp.company}</i> ({date_str})" if date_str else f"<b>{exp.title}</b> &mdash; <i>{exp.company}</i>"
                story.append(Paragraph(role_header, body_style))
                for bullet in exp.bullets:
                    story.append(Paragraph(f"&bull; {bullet}", body_style))
                story.append(Spacer(1, 4))

        # Education
        if resume.education:
            story.append(Paragraph("EDUCATION", section_style))
            for edu in resume.education:
                edu_date = f"{edu.start_date} - {edu.end_date}".strip(" -") if (edu.start_date or edu.end_date) else ""
                edu_header = f"<b>{edu.degree}</b> &mdash; {edu.institution} ({edu_date})" if edu_date else f"<b>{edu.degree}</b> &mdash; {edu.institution}"
                story.append(Paragraph(edu_header, body_style))

        # Skills
        if resume.skills:
            story.append(Paragraph("SKILLS", section_style))
            skills_str = ", ".join([s for cat in resume.skills for s in cat.skills])
            if skills_str:
                story.append(Paragraph(skills_str, body_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
