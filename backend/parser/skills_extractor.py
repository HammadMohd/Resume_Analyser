"""Skills extractor — extracts and categorizes skills from resume text.

This module identifies technical and soft skills mentioned in a resume,
categorizes them, and provides skill proficiency detection.

Responsibilities:
    - Extracting skills from text
    - Categorizing skills (languages, frameworks, tools, etc.)
    - Detecting skill proficiency levels
    - Matching skills against known skill database

NOT responsible for:
    - Extracting contact info (belongs to ner_extractor)
    - Parsing resume sections (belongs to section_detector)
"""

import re

from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Skill categories with known skills
SKILL_DATABASE: dict[str, list[str]] = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c", "c++", "c#",
        "ruby", "go", "golang", "rust", "kotlin", "swift", "scala",
        "php", "perl", "r", "matlab", "sql", "nosql", "dart", "elixir",
        "haskell", "clojure", "julia", "lua", "assembly", "fortran",
        "cobol", "pascal", "objective-c", "groovy", "powershell", "bash",
    ],
    "web_frameworks": [
        "react", "react.js", "reactjs", "angular", "angularjs", "vue", "vue.js", "vuejs",
        "svelte", "next.js", "nextjs", "nuxt", "nuxt.js",
        "node.js", "nodejs", "express", "express.js",
        "django", "flask", "fastapi", "bottle", "pyramid",
        "spring", "spring boot", "springboot",
        "rails", "ruby on rails", "sinatra",
        "laravel", "symfony", "codeigniter",
        "asp.net", "dotnet", ".net core", ".net",
        "blazor", "maui",
    ],
    "cloud_platforms": [
        "aws", "amazon web services", "ec2", "s3", "lambda", "ecs", "eks",
        "azure", "microsoft azure", "azure devops",
        "gcp", "google cloud", "google cloud platform",
        "heroku", "digitalocean", "linode", "vultr",
        "firebase", "supabase", "netlify", "vercel",
    ],
    "databases": [
        "postgresql", "postgres", "mysql", "mariadb", "sqlite",
        "mongodb", "mongo", "dynamodb", "couchdb", "cassandra",
        "redis", "memcached", "elasticsearch", "opensearch",
        "oracle", "sql server", "mssql", "snowflake", "bigquery",
        "neo4j", "influxdb", "timescaledb", "cockroachdb",
        "firebase firestore", "realm", "couchbase",
    ],
    "devops_tools": [
        "docker", "kubernetes", "k8s", "helm", "istio",
        "terraform", "pulumi", "cloudformation", "ansible", "chef", "puppet",
        "jenkins", "github actions", "gitlab ci", "circleci", "travis ci",
        "argo", "argo cd", "flux", "tekton",
        "prometheus", "grafana", "datadog", "new relic", "splunk",
        "nginx", "apache", "traefik", "haproxy",
    ],
    "data_science": [
        "machine learning", "ml", "deep learning", "dl",
        "natural language processing", "nlp", "computer vision", "cv",
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "jupyter", "jupyter notebook", "google colab",
        "spark", "pyspark", "hadoop", "kafka",
        "tableau", "power bi", "looker",
        "opencv", "pillow", "nltk", "spacy", "gensim",
    ],
    "mobile_development": [
        "ios", "android", "react native", "flutter", "dart",
        "xcode", "android studio", "swiftui", "uikit",
        "kotlin multiplatform", "kmm", "ionic", "cordova",
    ],
    "testing": [
        "pytest", "unittest", "jest", "mocha", "chai", "cypress", "playwright",
        "selenium", "junit", "testng", "mockito",
        "rspec", "minitest", "phpunit",
        "postman", "insomnia", "k6", "jmeter",
        "tdd", "bdd", "unit testing", "integration testing", "e2e testing",
    ],
    "version_control": [
        "git", "github", "gitlab", "bitbucket", "svn", "mercurial",
    ],
    "ide_and_editors": [
        "vscode", "visual studio code", "visual studio", "intellij", "idea",
        "pycharm", "webstorm", "vim", "neovim", "emacs", "sublime text",
        "atom", "notepad++",
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "collaboration",
        "problem solving", "problem-solving", "analytical", "critical thinking",
        "time management", "organization", "adaptability", "flexibility",
        "creativity", "innovation", "mentoring", "coaching",
        "presentation", "negotiation", "conflict resolution",
        "project management", "agile", "scrum", "kanban",
    ],
    "methodologies": [
        "agile", "scrum", "kanban", "waterfall", "lean", "six sigma",
        "tdd", "bdd", "ddd", "microservices", "serverless",
        "ci/cd", "devops", "mlops", "datops",
    ],
}

# Flatten all skills for quick lookup
ALL_SKILLS: set[str] = set()
for skills in SKILL_DATABASE.values():
    ALL_SKILLS.update(s.lower() for s in skills)

# Proficiency indicators
LEVEL_INDICATORS = {
    "expert": ["expert", "advanced", "proficient", "master", "10+ years", "8+ years"],
    "advanced": ["experienced", "strong", "5+ years", "7+ years", "4+ years"],
    "intermediate": ["familiar", "working knowledge", "basic", "2+ years", "3+ years"],
    "beginner": ["beginner", "learning", "exposed to", "introduction", "1+ year"],
}


class SkillsExtractor:
    """Extract and categorize skills from resume text."""

    def __init__(self) -> None:
        """Initialize with compiled patterns."""
        self._skill_patterns: dict[str, re.Pattern] = {}
        for skill in ALL_SKILLS:
            # Escape special chars and create word boundary pattern
            escaped = re.escape(skill)
            self._skill_patterns[skill] = re.compile(
                r"\b" + escaped + r"\b", re.IGNORECASE
            )

    def extract_skills(self, text: str) -> list[dict]:
        """Extract all skills from text with categories.

        Args:
            text: Resume text.

        Returns:
            List of dicts with 'skill', 'category', 'confidence' keys.
        """
        found_skills = []
        text_lower = text.lower()

        for skill in ALL_SKILLS:
            if skill in text_lower:
                pattern = self._skill_patterns[skill]
                matches = pattern.findall(text)
                if matches:
                    category = self._get_category(skill)
                    found_skills.append({
                        "skill": skill,
                        "category": category,
                        "confidence": min(1.0, len(matches) * 0.3 + 0.5),
                    })

        # Deduplicate
        seen = set()
        unique_skills = []
        for s in found_skills:
            if s["skill"] not in seen:
                seen.add(s["skill"])
                unique_skills.append(s)

        logger.info("Extracted %d skills", len(unique_skills))
        return unique_skills

    def extract_skills_by_category(self, text: str) -> dict[str, list[str]]:
        """Extract skills grouped by category.

        Args:
            text: Resume text.

        Returns:
            Dict mapping category names to lists of skills.
        """
        skills = self.extract_skills(text)
        categorized: dict[str, list[str]] = {}

        for s in skills:
            cat = s["category"]
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(s["skill"])

        return categorized

    def detect_proficiency(self, text: str, skill: str) -> str:
        """Detect proficiency level for a specific skill.

        Args:
            text: Resume text.
            skill: Skill to check.

        Returns:
            Proficiency level string.
        """
        text_lower = text.lower()
        skill_lower = skill.lower()

        # Find context around skill mention
        for level, indicators in LEVEL_INDICATORS.items():
            for indicator in indicators:
                # Check if indicator is near the skill mention
                pattern = re.compile(
                    r"(?i)" + re.escape(indicator) + r".{0,50}" + re.escape(skill_lower)
                    + r"|" + re.escape(skill_lower) + r".{0,50}" + re.escape(indicator),
                    re.IGNORECASE,
                )
                if pattern.search(text_lower):
                    return level

        return "not_specified"

    def _get_category(self, skill: str) -> str:
        """Get the category for a skill."""
        for category, skills in SKILL_DATABASE.items():
            if skill in [s.lower() for s in skills]:
                return category
        return "other"

    def get_skill_suggestions(self, text: str) -> list[str]:
        """Suggest skills that might be missing based on context.

        Args:
            text: Resume text.

        Returns:
            List of suggested skills.
        """
        found = {s["skill"] for s in self.extract_skills(text)}
        suggestions = []

        # Simple heuristic: if they have React, suggest related skills
        if "react" in found:
            if "typescript" not in found:
                suggestions.append("typescript")
            if "next.js" not in found:
                suggestions.append("next.js")

        if "python" in found:
            if "fastapi" not in found and "django" not in found:
                suggestions.append("fastapi")

        return suggestions
