"""Validation enhancer — consolidates issues and generates examples.

Takes raw per-bullet issues from the rule engine and:
1. Groups them into per-section summaries (not per-bullet noise)
2. Calls Gemini to generate 5 improved bullet examples
"""

from backend.llm import LLM_AVAILABLE
from backend.schemas.resume import NormalizedResume
from backend.schemas.rules import Issue, RuleResult
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Maps rule names to human-readable issue groups
_ISSUE_GROUPINGS = {
    "bullet_action_verb": {
        "message": "Some bullets don't start with action verbs",
        "suggestion": (
            "Start each bullet with a strong action verb "
            "like Led, Built, Designed, Implemented, Optimized"
        ),
    },
    "bullet_metrics": {
        "message": "Some bullets lack quantifiable metrics",
        "suggestion": "Add numbers, percentages, or measurable outcomes",
    },
    "bullet_too_short": {
        "message": "Some bullets are too short",
        "suggestion": "Expand with more details about your impact and results",
    },
    "bullet_too_long": {
        "message": "Some bullets are too long",
        "suggestion": "Keep bullets concise — 1 to 2 lines ideally",
    },
    "bullets_exist": {
        "message": "No bullet points found in experience section",
        "suggestion": (
            "Add bullet points describing your achievements "
            "with action verbs and metrics"
        ),
    },
}


def enhance_validation(
    rule_result: RuleResult,
    resume: NormalizedResume,
) -> dict:
    """Consolidate issues and generate examples.

    Returns a dict with:
      - consolidated_issues: list of grouped issues (one per problem type per section)
      - bullet_examples: list of 5 improved bullet examples (if LLM available)
    """
    consolidated = _consolidate_issues(rule_result.all_issues)
    examples = _generate_bullet_examples(resume) if LLM_AVAILABLE else []

    return {
        "consolidated_issues": consolidated,
        "bullet_examples": examples,
    }


def _consolidate_issues(issues: list[Issue]) -> list[dict]:
    """Group per-bullet issues into single summaries per section + rule type.

    Instead of:
      [experience] Bullet 1 doesn't start with an action verb
      [experience] Bullet 2 doesn't start with an action verb
      [experience] Bullet 3 lacks quantifiable metrics

    Produces:
      [experience] 2 bullets don't start with action verbs
      [experience] 1 bullet lacks quantifiable metrics
    """
    # Group by (section, rule_type)
    groups: dict[tuple[str, str], list[Issue]] = {}
    non_bullet_issues: list[Issue] = []

    for issue in issues:
        if issue.rule.startswith("bullet_"):
            key = (issue.section, issue.rule)
            groups.setdefault(key, []).append(issue)
        else:
            non_bullet_issues.append(issue)

    consolidated: list[dict] = []

    # Add non-bullet issues as-is (contact, summary, etc.)
    for issue in non_bullet_issues:
        consolidated.append({
            "section": issue.section,
            "severity": issue.severity,
            "message": issue.message,
            "suggestion": issue.suggestion,
        })

    # Consolidate bullet issues
    for (section, rule), group_issues in groups.items():
        count = len(group_issues)
        mapping = _ISSUE_GROUPINGS.get(rule, {})
        msg_template = mapping.get("message", f"{count} bullet issue(s) found")
        suggestion = mapping.get("suggestion", "")

        # Make message count-aware
        if count == 1:
            message = (
                msg_template
                .replace("Some bullets", "A bullet")
                .replace("Some bullet", "A bullet")
            )
        else:
            message = (
                msg_template
                .replace("Some bullets", f"{count} bullets")
                .replace("Some bullet", f"{count} bullets")
            )

        consolidated.append({
            "section": section,
            "severity": group_issues[0].severity,
            "message": message,
            "suggestion": suggestion,
        })

    # Sort: errors first, then warnings, then info
    severity_order = {"error": 0, "warning": 1, "info": 2}
    consolidated.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return consolidated


def _generate_bullet_examples(resume: NormalizedResume) -> list[dict]:
    """Use Gemini to generate 5 improved bullet examples from the resume."""
    bullets = []
    for exp in resume.experience:
        bullets.extend(exp.bullets)

    if not bullets:
        return []

    try:
        import json
        import re

        import google.generativeai as genai

        from backend.config.settings import settings

        skills_text = ""
        for cat in resume.skills:
            skills_text += ", ".join(cat.skills) + ", "

        prompt = f"""You are a resume writing expert. Given these resume bullet points and skills,
rewrite exactly 5 of them into improved versions.

RULES:
- Each improved bullet MUST start with a strong action verb
- Each improved bullet MUST include specific numbers, percentages, or metrics
- Each improved bullet MUST mention a relevant technology or skill
- Keep each bullet to 1-2 lines
- Return ONLY a JSON array of objects with "original" and "improved" keys

Skills: {skills_text}

Original bullets:
"""
        for i, b in enumerate(bullets[:8]):
            prompt += f"{i + 1}. {b}\n"

        prompt += '\nReturn format: [{"original": "...", "improved": "..."}, ...]'

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(prompt)

        content = response.text
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            examples = json.loads(json_match.group())
            return examples[:5]

    except Exception as e:
        logger.warning("Failed to generate bullet examples: %s", e)

    return _generate_rule_based_examples(bullets[:5])


def _generate_rule_based_examples(bullets: list[str]) -> list[dict]:
    """Generate improved bullet examples using rules when LLM is unavailable."""
    import re

    action_verbs = [
        "Developed", "Implemented", "Built", "Optimized", "Led",
        "Designed", "Automated", "Streamlined", "Delivered", "Enhanced",
    ]
    metric_templates = [
        "resulting in a {}% improvement",
        "serving {}+ users",
        "reducing processing time by {}%",
        "saving {} hours per week",
        "handling {}+ records daily",
    ]

    examples = []
    for bullet in bullets:
        improved = bullet
        changes = []

        # Fix action verb
        words = bullet.split()
        if words and words[0].lower() not in _ACTION_VERBS:
            for verb in action_verbs:
                if verb.lower() in bullet.lower():
                    improved = verb + " " + bullet.lower().split(verb.lower(), 1)[-1].strip()
                    changes.append("action verb")
                    break
            else:
                improved = "Developed " + bullet[0].lower() + bullet[1:]
                changes.append("action verb")

        # Add metrics placeholder
        has_metrics = any(
            p.search(improved)
            for p in [
                re.compile(r"\d+%"),
                re.compile(r"\d+\s*(?:users|records|requests|hours|days|weeks|months)"),
            ]
        )
        if not has_metrics:
            import random
            template = random.choice(metric_templates)
            number = random.choice([25, 30, 40, 50, 100, 200, 500])
            improved = improved.rstrip(".")
            improved += f", {template.format(number)}."
            changes.append("metrics")

        if improved != bullet:
            examples.append({"original": bullet, "improved": improved})

    return examples[:5]


# Action verbs for rule-based fallback
_ACTION_VERBS = {
    "achieved", "added", "built", "collaborated", "created", "delivered",
    "designed", "developed", "drove", "enhanced", "established", "executed",
    "generated", "grew", "guided", "implemented", "improved", "increased",
    "initiated", "integrated", "introduced", "launched", "led", "managed",
    "migrated", "optimized", "orchestrated", "performed", "planned",
    "produced", "reduced", "refactored", "resolved", "saved", "secured",
    "simplified", "solved", "standardized", "strengthened", "tested",
    "trained", "transformed", "updated", "upgraded", "utilized", "verified",
    "wrote",
}
