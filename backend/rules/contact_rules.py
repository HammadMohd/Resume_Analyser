"""Contact rules — validates contact information completeness.

Checks for presence of email, phone, LinkedIn, and GitHub.
Each contact method contributes to the contact score.

Scoring:
- Email present: 30 points
- Phone present: 30 points
- LinkedIn present: 25 points
- GitHub present: 15 points
"""

from backend.schemas.resume import ContactInfo
from backend.schemas.rules import Issue, RuleOutput
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def evaluate_contact(contact: ContactInfo) -> RuleOutput:
    """Evaluate contact information completeness.

    Args:
        contact: Contact information from normalized resume.

    Returns:
        RuleOutput with score and issues.
    """
    issues: list[Issue] = []
    checks_passed = 0
    checks_total = 4

    # Check email
    if contact.email:
        checks_passed += 1
    else:
        issues.append(
            Issue(
                rule="contact_email",
                severity="error",
                message="No email address found",
                section="contact",
                suggestion="Add a professional email address to your resume",
            )
        )

    # Check phone
    if contact.phone:
        checks_passed += 1
    else:
        issues.append(
            Issue(
                rule="contact_phone",
                severity="error",
                message="No phone number found",
                section="contact",
                suggestion="Add a phone number with country code",
            )
        )

    # Check LinkedIn
    if contact.linkedin:
        checks_passed += 1
    else:
        issues.append(
            Issue(
                rule="contact_linkedin",
                severity="warning",
                message="No LinkedIn profile found",
                section="contact",
                suggestion="Add your LinkedIn profile URL to increase visibility",
            )
        )

    # Check GitHub (optional but recommended for tech roles)
    if contact.github:
        checks_passed += 1
    else:
        issues.append(
            Issue(
                rule="contact_github",
                severity="info",
                message="No GitHub profile found",
                section="contact",
                suggestion="Consider adding GitHub for technical roles",
            )
        )

    # Calculate score
    score = (checks_passed / checks_total) * 100

    logger.info("Contact score: %.0f/100 (%d/%d checks)", score, checks_passed, checks_total)

    return RuleOutput(
        category="contact",
        passed=checks_passed == checks_total,
        score=score,
        max_score=100,
        issues=issues,
        checks_passed=checks_passed,
        checks_total=checks_total,
    )
