"""Structured parser — extracts structured data from resume sections.

This module takes raw section text and extracts structured information
like contact details, experience entries, education records, and skills.

Responsibilities:
    - Extracting contact info (name, email, phone, LinkedIn, etc.)
    - Parsing experience entries (company, title, dates, bullets)
    - Parsing education entries (institution, degree, dates)
    - Extracting skills by category

NOT responsible for:
    - Detecting section boundaries (belongs to section_detector)
    - Running OCR or file parsing (belongs to parser module)
"""

import re

from backend.parser.section_detector import SectionDetector
from backend.schemas.resume import (
    ContactInfo,
    Education,
    Experience,
    NormalizedResume,
    Project,
    ResumeSection,
    SkillCategory,
)
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Email pattern
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Phone patterns - requires country code prefix (+XX or 0), 10 digits, or US 3-3-4 format
PHONE_PATTERN = re.compile(
    r"\+\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
    r"|0\d{10}"
    r"|\d{10}"
    r"|\d{3}[-.\s]\d{3}[-.\s]\d{4}"
    r"|\(\d{3,4}\)[-. ]?\d{3,4}[-.\s]?\d{4}"
)

# LinkedIn pattern - full URLs, short URLs, and bare domain
LINKEDIN_PATTERN = re.compile(
    r"(?:https?://(?:www\.)?(?:linkedin\.com/(?:in|profile)/[a-zA-Z0-9_-]+"
    r"|rb\.gy/[a-zA-Z0-9_-]+))"
    r"|linkedin\.com/in/[a-zA-Z0-9_-]+",
    re.IGNORECASE,
)

# GitHub pattern - URLs and text mentions like "username (github.com)"
GITHUB_PATTERN = re.compile(
    r"(?:https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+)"
    r"|github\.com/[a-zA-Z0-9_-]+"
    r"|([a-zA-Z0-9_-]+)\s*\(github\.com\)",
    re.IGNORECASE,
)

# Date patterns
DATE_RANGE_PATTERN = re.compile(
    r"(\w+\s+\d{4}|\d{4})\s*[-–—]\s*(\w+\s+\d{4}|\d{4}|present|current)",
    re.IGNORECASE,
)

# Bullet patterns
BULLET_PATTERN = re.compile(r"^[\s]*[-•●▪▸→*]\s+(.+)$")

# Skill category patterns
SKILL_CATEGORY_PATTERN = re.compile(r"^([A-Za-z\s/]+):\s*(.+)$")


class StructuredParser:
    """Parse resume sections into structured data."""

    def __init__(self) -> None:
        """Initialize section detector."""
        self.detector = SectionDetector()

    def parse_resume(self, text: str, filename: str = "") -> NormalizedResume:
        """Parse raw text into normalized resume.

        Args:
            text: Full resume text.
            filename: Original filename.

        Returns:
            Fully normalized resume object.
        """
        import time

        start = time.time()

        sections = self.detector.detect_sections(text)

        resume = NormalizedResume(
            filename=filename,
            summary="",
            raw_text=text,
            normalization_time_ms=0,
        )

        # Extract each section
        for section in sections:
            section_text = self._get_section_text(text, section)
            resume.sections_detected.append(
                ResumeSection(
                    section_type=section["type"],
                    title=section["title"],
                    content=section_text,
                    confidence=1.0,
                )
            )

            if section["type"] == "contact":
                resume.contact = self._parse_contact(section_text, text)
            elif section["type"] == "summary":
                resume.summary = section_text
            elif section["type"] == "experience":
                resume.experience = self._parse_experience(section_text)
            elif section["type"] == "education":
                resume.education = self._parse_education(section_text)
            elif section["type"] == "skills":
                resume.skills = self._parse_skills(section_text)
            elif section["type"] == "projects":
                resume.projects = self._parse_projects(section_text)

        # If no contact section found, try to extract from full text
        if not resume.contact.name:
            resume.contact = self._parse_contact("", text)

        elapsed = (time.time() - start) * 1000
        resume.normalization_time_ms = round(elapsed, 2)
        logger.info("Resume normalized in %.2f ms", elapsed)

        return resume

    def _get_section_text(self, text: str, section: dict) -> str:
        """Get text content of a section.

        Handles both standalone headers and headers with inline content
        (e.g., 'Skills: Python, Java, SQL' extracts 'Python, Java, SQL').
        """
        lines = text.split("\n")
        start = section["start"] + 1
        end = section["end"]
        body = "\n".join(lines[start:end]).strip()

        # If body is empty, check if header line has inline content after ':'
        header_line = lines[section["start"]].strip()
        if ":" in header_line and not body:
            after_colon = header_line.split(":", 1)[1].strip()
            if after_colon:
                body = after_colon

        return body

    def _parse_contact(self, section_text: str, full_text: str) -> ContactInfo:
        """Extract contact information."""
        text_to_search = f"{section_text}\n{full_text}"

        # Extract email
        email_match = EMAIL_PATTERN.search(text_to_search)
        email = email_match.group() if email_match else ""

        # Extract phone
        phone_match = PHONE_PATTERN.search(text_to_search)
        phone = phone_match.group() if phone_match else ""

        # Extract LinkedIn
        linkedin_match = LINKEDIN_PATTERN.search(text_to_search)
        linkedin = linkedin_match.group() if linkedin_match else ""

        # Extract GitHub (may be URL or text mention like "user (github.com)")
        github_match = GITHUB_PATTERN.search(text_to_search)
        if github_match:
            # group(1) is the username from text mention
            username = (
                github_match.group(1)
                if github_match.lastindex and github_match.group(1)
                else None
            )
            github = f"github.com/{username}" if username else github_match.group()
        else:
            github = ""

        # Extract name (first non-empty line in contact section)
        name = ""
        if section_text:
            for line in section_text.split("\n"):
                stripped = line.strip()
                if (
                    stripped
                    and not EMAIL_PATTERN.search(stripped)
                    and not PHONE_PATTERN.search(stripped)
                ):
                    name = stripped
                    break

        # Extract location (common patterns)
        location = ""
        location_patterns = [
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2})",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text_to_search)
            if match:
                location = match.group()
                break

        return ContactInfo(
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github,
            location=location,
            website="",
        )

    def _parse_experience(self, text: str) -> list[Experience]:
        """Parse experience section into entries."""
        entries = []
        current = None

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # Check for bullet
            bullet_match = BULLET_PATTERN.match(stripped)
            if bullet_match:
                if current:
                    current.bullets.append(bullet_match.group(1))
                else:
                    # Bullet before any header — create a default entry
                    current = Experience(
                        company="",
                        title="",
                        location="",
                        start_date="",
                        end_date="",
                        description="",
                    )
                    current.bullets.append(bullet_match.group(1))
                continue

            # Check for date range (indicates new entry or header)
            date_match = DATE_RANGE_PATTERN.search(stripped)
            if date_match or self._looks_like_job_header(stripped):
                # If current entry has title but no date, and this line has a date,
                # merge into current entry instead of creating new
                if current and current.title and not current.start_date and date_match:
                    current.start_date = date_match.group(1)
                    current.end_date = date_match.group(2)
                    # Try to extract company from the remaining text before date
                    before_date = stripped[:date_match.start()].strip().rstrip(",").strip()
                    if before_date and not current.company:
                        for sep in [" at ", " @ ", " | ", " - ", " — "]:
                            if sep in before_date:
                                parts = before_date.split(sep, 1)
                                current.company = parts[0].strip()
                                current.location = parts[1].strip()
                                break
                        if not current.company:
                            current.company = before_date
                    continue

                if current:
                    entries.append(current)

                current = Experience(
                    company="",
                    title="",
                    location="",
                    start_date=date_match.group(1) if date_match else "",
                    end_date=date_match.group(2) if date_match else "",
                    description="",
                )
                current.start_date = date_match.group(1) if date_match else ""
                current.end_date = date_match.group(2) if date_match else ""

                # Try to split company and title
                parts = self._split_company_title(stripped, date_match)
                current.company = parts.get("company", "")
                current.title = parts.get("title", "")

            # Check if line looks like a company (contains "|" or "at")
            elif current and current.title and not current.company:
                for sep in [" at ", " @ ", " | "]:
                    if sep in stripped:
                        parts = stripped.split(sep, 1)
                        current.company = parts[0].strip()
                        current.location = parts[1].strip() if len(parts) > 1 else ""
                        break
                else:
                    current.description = stripped
            elif current and not current.description:
                current.description = stripped

        if current:
            entries.append(current)

        logger.info("Parsed %d experience entries", len(entries))
        return entries

    def _looks_like_job_header(self, line: str) -> bool:
        """Heuristic to detect job header lines."""
        # Contains common job title words
        job_words = [
            "engineer",
            "developer",
            "manager",
            "analyst",
            "lead",
            "senior",
            "junior",
            "staff",
            "principal",
            "director",
            "intern",
            "consultant",
            "architect",
        ]
        line_lower = line.lower()
        return any(word in line_lower for word in job_words)

    def _split_company_title(self, text: str, date_match: re.Match | None) -> dict:
        """Split a line into company and title."""
        if date_match:
            text = text[: date_match.start()].strip().rstrip(",").strip()

        # Common separators
        for sep in [" at ", " @ ", " | ", " - ", " — "]:
            if sep in text:
                parts = text.split(sep, 1)
                return {"title": parts[0].strip(), "company": parts[1].strip().rstrip(",")}

        # If only one part, treat as title
        return {"title": text.rstrip(","), "company": ""}

    def _parse_education(self, text: str) -> list[Education]:
        """Parse education section into entries."""
        entries = []
        current = None

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            date_match = DATE_RANGE_PATTERN.search(stripped)
            if date_match or self._looks_like_education_header(stripped):
                if current:
                    entries.append(current)

                current = Education(
                    institution="",
                    degree="",
                    field_of_study="",
                    start_date=date_match.group(1) if date_match else "",
                    end_date=date_match.group(2) if date_match else "",
                    gpa="",
                    description="",
                )
                current.start_date = date_match.group(1) if date_match else ""
                current.end_date = date_match.group(2) if date_match else ""

                # Try to extract institution and degree
                text_without_dates = stripped
                if date_match:
                    text_without_dates = stripped[: date_match.start()].strip()

                parts = self._split_degree_institution(text_without_dates)
                current.degree = parts.get("degree", "")
                current.institution = parts.get("institution", "")
            elif current and not current.description:
                current.description = stripped

        if current:
            entries.append(current)

        logger.info("Parsed %d education entries", len(entries))
        return entries

    def _looks_like_education_header(self, line: str) -> bool:
        """Heuristic to detect education header lines."""
        edu_words = [
            "university",
            "college",
            "institute",
            "school",
            "bachelor",
            "master",
            "phd",
            "degree",
            "bs",
            "ba",
            "ms",
            "mba",
        ]
        line_lower = line.lower()
        return any(word in line_lower for word in edu_words)

    def _split_degree_institution(self, text: str) -> dict:
        """Split text into degree and institution."""
        for sep in [" from ", " @ ", " | "]:
            if sep in text:
                parts = text.split(sep, 1)
                return {"degree": parts[0].strip(), "institution": parts[1].strip().rstrip(",")}

        # Handle comma separation
        if ", " in text:
            parts = text.split(", ", 1)
            return {"degree": parts[0].strip(), "institution": parts[1].strip().rstrip(",")}

        return {"degree": text.rstrip(","), "institution": ""}

    def _parse_skills(self, text: str) -> list[SkillCategory]:
        """Parse skills section into categorized skills."""
        categories = []

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # Check for category: skills pattern
            cat_match = SKILL_CATEGORY_PATTERN.match(stripped)
            if cat_match:
                category = cat_match.group(1).strip()
                skills_text = cat_match.group(2).strip()
                skills = [s.strip() for s in re.split(r"[,;|]", skills_text) if s.strip()]
                categories.append(SkillCategory(category=category, skills=skills))
            else:
                # Treat as flat skill list
                skills = [s.strip() for s in re.split(r"[,;|]", stripped) if s.strip()]
                if skills:
                    categories.append(SkillCategory(category="General", skills=skills))

        logger.info("Parsed %d skill categories", len(categories))
        return categories

    def _parse_projects(self, text: str) -> list[Project]:
        """Parse projects section into entries."""
        entries = []
        current = None

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            bullet_match = BULLET_PATTERN.match(stripped)
            if bullet_match:
                bullet_text = bullet_match.group(1)
                # If bullet contains ":", treat as project name: description
                if ":" in bullet_text and not current:
                    name, desc = bullet_text.split(":", 1)
                    current = Project(name=name.strip(), description=desc.strip(), url="")
                    entries.append(current)
                    current = None
                elif current:
                    current.bullets.append(bullet_text)
                continue

            # Skip "Tech Stack:" and similar metadata lines
            if re.match(r"^(tech\s+stack|technology|technologies|tools)\s*:", stripped, re.IGNORECASE):
                if current:
                    current.description = stripped
                continue

            # New project
            if current:
                entries.append(current)

            current = Project(name=stripped, description="", url="")

        if current:
            entries.append(current)

        logger.info("Parsed %d project entries", len(entries))
        return entries
