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

    prompt = f"""You are a professional resume writer. Rewrite the following bullet point to be more impactful and ATS-friendly.

Rules:
1. Start with a strong action verb
2. Include quantifiable metrics if possible (but do NOT invent fake numbers)
3. Keep it concise (1-2 lines max)
4. Do NOT add technologies or skills not mentioned in the original
5. Do NOT fabricate experience or achievements
6. Return ONLY valid JSON with the specified format

{context_text}{skills_text}

Original bullet:
"{original}"

Return your response as JSON:
{{
  "improved": "Your improved bullet here",
  "changes_made": ["list of changes made"],
  "confidence": 0.8
}}"""

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
    bullets_text = "\n".join(
        f'{i+1}. "{b["original"]}"' for i, b in enumerate(bullets)
    )

    jd_context = ""
    if job_description:
        # Truncate JD to avoid token limits
        jd_short = job_description[:500] + "..." if len(job_description) > 500 else job_description
        jd_context = f"\nJob Description Context:\n{jd_short}"

    prompt = f"""You are a professional resume writer. Rewrite the following bullet points to be more impactful and ATS-friendly.

Target Role: {job_title or "Not specified"}
{jd_context}

Rules:
1. Start each bullet with a strong action verb
2. Include quantifiable metrics ONLY if they exist in the original
3. Keep bullets concise (1-2 lines max)
4. Do NOT add technologies or skills not in the original
5. Do NOT fabricate experience or achievements
6. Return ONLY valid JSON with the specified format

Original Bullets:
{bullets_text}

Return your response as JSON:
{{
  "rewritten": [
    {{
      "original": "original bullet 1",
      "improved": "improved bullet 1",
      "changes_made": ["change 1", "change 2"],
      "confidence": 0.8
    }}
  ]
}}"""

    return prompt
