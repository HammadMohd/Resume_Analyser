"""Section rules — validates required resume sections are present.

ATS systems expect specific sections to exist in a resume.
Missing sections can cause automatic rejection.

Required sections:
- Experience (most important)
- Skills (most important)
- Education (important)

Recommended sections:
- Summary/Objective

Scoring:
- Experience present: 35 points
- Skills present: 30 points
- Education present: 25 points
- Summary present: 10 points
"""

from backend.schemas.resume import NormalizedResume
from backend.schemas.rules import Issue, RuleOutput
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Required sections with their weights
REQUIRED_SECTIONS = {
    "experience": {"weight": 35, "severity": "error", "name": "Work Experience"},
    "skills": {"weight": 30, "severity": "error", "name": "Skills"},
    "education": {"weight": 25, "severity": "error", "name": "Education"},
}

RECOMMENDED_SECTIONS = {
    "summary": {"weight": 10, "severity": "warning", "name": "Professional Summary"},
}


def evaluate_sections(resume: NormalizedResume) -> RuleOutput:
    """Evaluate resume section completeness.

    Args:
        resume: Normalized resume data.

    Returns:
        RuleOutput with score and issues.
    """
    issues: list[Issue] = []
    checks_passed = 0
    checks_total = len(REQUIRED_SECTIONS) + len(RECOMMENDED_SECTIONS)
    score = 0.0

    # Check required sections
    for section_type, config in REQUIRED_SECTIONS.items():
        section_data = getattr(resume, section_type, None)
        if section_data and len(section_data) > 0:
            checks_passed += 1
            score += config["weight"]
        else:
            issues.append(
                Issue(
                    rule=f"section_{section_type}",
                    severity=config["severity"],
                    message=f"Missing required section: {config['name']}",
                    section=section_type,
                    suggestion=f"Add a {config['name']} section to your resume",
                )
            )

    # Check recommended sections
    for section_type, config in RECOMMENDED_SECTIONS.items():
        section_data = getattr(resume, section_type, "")
        if section_data:
            checks_passed += 1
            score += config["weight"]
        else:
            issues.append(
                Issue(
                    rule=f"section_{section_type}",
                    severity=config["severity"],
                    message=f"Missing recommended section: {config['name']}",
                    section=section_type,
                    suggestion=f"Consider adding a {config['name']} section",
                )
            )

    logger.info("Section score: %.0f/100 (%d/%d checks)", score, checks_passed, checks_total)

    return RuleOutput(
        category="sections",
        passed=checks_passed == checks_total,
        score=score,
        max_score=100,
        issues=issues,
        checks_passed=checks_passed,
        checks_total=checks_total,
    )
