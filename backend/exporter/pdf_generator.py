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
        email = resume.contact.email or ""
        phone = resume.contact.phone or ""
        location = resume.contact.location or ""
        contact_str = f"{email} | {phone} | {location}"
        story.append(Paragraph(resume.contact.name or "Candidate Resume", title_style))
        story.append(Paragraph(contact_str, subtitle_style))
        story.append(Spacer(1, 6))

        # Experience
        if resume.experience:
            story.append(Paragraph("WORK EXPERIENCE", section_style))
            for exp in resume.experience:
                exp_start = exp.start_date
                exp_end = exp.end_date
                date_str = (
                    f"{exp_start} - {exp_end}".strip(" -")
                    if (exp_start or exp_end)
                    else ""
                )
                title_bold = f"<b>{exp.title}</b>"
                company_it = f"<i>{exp.company}</i>"
                if date_str:
                    role_header = (
                        f"{title_bold} &mdash; {company_it}"
                        f" ({date_str})"
                    )
                else:
                    role_header = (
                        f"{title_bold} &mdash; {company_it}"
                    )
                story.append(Paragraph(role_header, body_style))
                for bullet in exp.bullets:
                    story.append(Paragraph(f"&bull; {bullet}", body_style))
                story.append(Spacer(1, 4))

        # Education
        if resume.education:
            story.append(Paragraph("EDUCATION", section_style))
            for edu in resume.education:
                edu_start = edu.start_date
                edu_end = edu.end_date
                edu_date = (
                    f"{edu_start} - {edu_end}".strip(" -")
                    if (edu_start or edu_end)
                    else ""
                )
                deg_bold = f"<b>{edu.degree}</b>"
                if edu_date:
                    edu_header = (
                        f"{deg_bold} &mdash;"
                        f" {edu.institution} ({edu_date})"
                    )
                else:
                    edu_header = (
                        f"{deg_bold} &mdash; {edu.institution}"
                    )
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
