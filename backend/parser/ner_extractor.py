"""NER entity extractor — extracts named entities from resume text.

This module uses NLP to extract person names, organizations,
locations, and other named entities from resume content.

Responsibilities:
    - Extracting person names
    - Extracting organization names
    - Extracting locations
    - Extracting dates and time periods

NOT responsible for:
    - Skills extraction (belongs to skills_extractor)
    - Section detection (belongs to section_detector)
"""

import re

from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Email pattern
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

# Phone patterns - supports international formats
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
)

# URL patterns
URL_RE = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+"
)

# LinkedIn - multiple formats
LINKEDIN_RE = re.compile(
    r"(?:https?://(?:www\.)?)?linkedin\.com/(?:in|profile)/[a-zA-Z0-9_-]+", re.IGNORECASE
)

# GitHub - multiple formats
GITHUB_RE = re.compile(
    r"(?:https?://(?:www\.)?)?github\.com/[a-zA-Z0-9_-]+", re.IGNORECASE
)

# Date patterns
DATE_PATTERNS = [
    # Month Year - Month Year
    re.compile(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})"
        r"\s*[-–—to]+\s*"
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|present|current|now)",
        re.IGNORECASE,
    ),
    # Month Year - Present
    re.compile(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})"
        r"\s*[-–—to]+\s*"
        r"(present|current|now)",
        re.IGNORECASE,
    ),
    # YYYY - YYYY
    re.compile(r"(\d{4})\s*[-–—to]+\s*(\d{4}|present|current|now)", re.IGNORECASE),
    # Month YYYY
    re.compile(
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}",
        re.IGNORECASE,
    ),
    # Just YYYY
    re.compile(r"\b(19|20)\d{2}\b"),
]

# Skill keywords (common technical skills)
TECH_SKILLS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "golang",
    "rust", "kotlin", "swift", "scala", "php", "perl", "r", "matlab", "sql",
    "html", "css", "scss", "sass", "less",
    "react", "angular", "vue", "vue.js", "svelte", "next.js", "nuxt",
    "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring",
    "rails", "laravel", "asp.net", "dotnet",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "ci/cd", "github actions",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
    "sqlite", "oracle", "sql server",
    "git", "github", "gitlab", "bitbucket",
    "linux", "unix", "bash", "powershell",
    "machine learning", "deep learning", "nlp", "natural language processing",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "graphql", "rest", "restful", "api", "microservices",
    "agile", "scrum", "jira", "confluence",
}

# Common job titles for name detection heuristics
JOB_TITLE_WORDS = {
    "engineer", "developer", "manager", "analyst", "lead", "senior",
    "junior", "staff", "principal", "director", "intern", "consultant",
    "architect", "scientist", "designer", "coordinator", "specialist",
    "assistant", "associate", "executive", "officer", "head", "vp",
}


class NERExtractor:
    """Extract named entities from resume text."""

    def extract_entities(self, text: str) -> dict:
        """Extract all entities from text.

        Args:
            text: Resume text.

        Returns:
            Dict with keys: emails, phones, urls, linkedin, github, dates.
        """
        entities = {
            "emails": self.extract_emails(text),
            "phones": self.extract_phones(text),
            "urls": self.extract_urls(text),
            "linkedin": self.extract_linkedin(text),
            "github": self.extract_github(text),
            "dates": self.extract_dates(text),
        }

        logger.info("Extracted entities: %s", {k: len(v) for k, v in entities.items()})
        return entities

    def extract_emails(self, text: str) -> list[str]:
        """Extract email addresses."""
        return list(set(EMAIL_RE.findall(text)))

    def extract_phones(self, text: str) -> list[str]:
        """Extract phone numbers."""
        return list(set(PHONE_RE.findall(text)))

    def extract_urls(self, text: str) -> list[str]:
        """Extract URLs."""
        urls = URL_RE.findall(text)
        # Filter out LinkedIn/GitHub (handled separately)
        return [u for u in urls if "linkedin.com" not in u and "github.com" not in u]

    def extract_linkedin(self, text: str) -> list[str]:
        """Extract LinkedIn profile URLs."""
        return list(set(LINKEDIN_RE.findall(text)))

    def extract_github(self, text: str) -> list[str]:
        """Extract GitHub profile URLs."""
        return list(set(GITHUB_RE.findall(text)))

    def extract_dates(self, text: str) -> list[dict]:
        """Extract date ranges from text.

        Returns:
            List of dicts with 'start', 'end', 'raw' keys.
        """
        dates = []
        seen = set()

        for pattern in DATE_PATTERNS:
            for match in pattern.finditer(text):
                raw = match.group(0)
                if raw in seen:
                    continue
                seen.add(raw)

                groups = match.groups()
                date_info = {"raw": raw, "start": "", "end": ""}

                if len(groups) >= 2:
                    date_info["start"] = groups[0]
                    date_info["end"] = groups[1]
                elif len(groups) == 1:
                    date_info["start"] = groups[0]

                dates.append(date_info)

        return dates

    def extract_phone_from_section(self, section_text: str) -> str:
        """Extract first phone number from section text."""
        phones = self.extract_phones(section_text)
        return phones[0] if phones else ""

    def extract_email_from_section(self, section_text: str) -> str:
        """Extract first email from section text."""
        emails = self.extract_emails(section_text)
        return emails[0] if emails else ""
