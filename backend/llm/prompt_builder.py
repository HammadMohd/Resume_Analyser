"""Prompt builder — constructs structured prompts for LLMs.

This module creates well-crafted prompts that guide LLMs
to produce consistent, validatable outputs.

Key principles:
- Be specific about output format
- Provide examples when possible
- Set clear constraints
- Request JSON output for validation
"""

from backend.utils.logging import get_logger

logger = get_logger(__name__)


def build_bullet_rewrite_prompt(
    original: str,
    context: str = "",
    missing_skills: list[str] | None = None,
) -> str:
    """Build a prompt for rewriting a single bullet point.

    Args:
        original: Original bullet text.
        context: Job title or context.
        missing_skills: Skills to incorporate if relevant.

    Returns:
        Formatted prompt string.
    """
    skills_text = ""
    if missing_skills:
        skills_text = f"\nRelevant skills to highlight: {', '.join(missing_skills)}"

    context_text = ""
    if context:
        context_text = f"\nTarget role: {context}"

    prompt = (
        "You are a professional resume writer. Rewrite the following bullet point "
        "to be more impactful and ATS-friendly.\n\n"
        "Rules:\n"
        "1. Start with a strong action verb\n"
        "2. Include quantifiable metrics if possible (but do NOT invent fake numbers)\n"
        "3. Keep it concise (1-2 lines max)\n"
        "4. Do NOT add technologies or skills not mentioned in the original\n"
        "5. Do NOT fabricate experience or achievements\n"
        "6. Return ONLY valid JSON with the specified format\n\n"
        f"{context_text}{skills_text}\n\n"
        f'Original bullet:\n"{original}"\n\n'
        "Return your response as JSON:\n"
        '{\n  "improved": "Your improved bullet here",\n'
        '  "changes_made": ["list of changes made"],\n'
        '  "confidence": 0.8\n}'
    )

    return prompt


def build_multi_bullet_rewrite_prompt(
    bullets: list[dict],
    job_title: str = "",
    job_description: str = "",
) -> str:
    """Build a prompt for rewriting multiple bullet points.

    Args:
        bullets: List of dicts with 'original' and optional 'context' keys.
        job_title: Target job title.
        job_description: Job description for context.

    Returns:
        Formatted prompt string.
    """
    bullets_text = "\n".join(f'{i + 1}. "{b["original"]}"' for i, b in enumerate(bullets))

    jd_context = ""
    if job_description:
        # Truncate JD to avoid token limits
        jd_short = job_description[:500] + "..." if len(job_description) > 500 else job_description
        jd_context = f"\nJob Description Context:\n{jd_short}"

    prompt = (
        "You are a professional resume writer. Rewrite the following bullet points "
        "to be more impactful and ATS-friendly.\n\n"
        f"Target Role: {job_title or 'Not specified'}\n"
        f"{jd_context}\n\n"
        "Rules:\n"
        "1. Start each bullet with a strong action verb\n"
        "2. Include quantifiable metrics ONLY if they exist in the original\n"
        "3. Keep bullets concise (1-2 lines max)\n"
        "4. Do NOT add technologies or skills not in the original\n"
        "5. Do NOT fabricate experience or achievements\n"
        "6. Return ONLY valid JSON with the specified format\n\n"
        f"Original Bullets:\n{bullets_text}\n\n"
        "Return your response as JSON:\n"
        '{\n  "rewritten": [\n    {\n'
        '      "original": "original bullet 1",\n'
        '      "improved": "improved bullet 1",\n'
        '      "changes_made": ["change 1", "change 2"],\n'
        '      "confidence": 0.8\n'
        "    }\n  ]\n}"
    )

    return prompt
