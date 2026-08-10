"""STAR Method Bullet Enhancer using Google Gemini API or Rule Fallback.

Re-architects experience bullet points using the STAR methodology:
- Situation / Task: High-context problem domain
- Action: Specific technology & leadership actions taken
- Result: Quantified impact metrics and outcome
"""

import json
import re

from pydantic import BaseModel

from backend.llm import LLM_AVAILABLE
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class STAREnhancementResult(BaseModel):
    original_bullet: str
    star_bullet: str
    target_skill_added: str | None
    quantified_metric_added: bool
    changes_made: list[str]


class STARBulletEnhancer:
    """Enhances resume bullets into high-impact STAR framework statements."""

    def enhance_bullet(
        self,
        original_bullet: str,
        target_skill: str | None = None,
        job_context: str | None = None,
    ) -> STAREnhancementResult:
        """Transform a single bullet point using LLM or rule-based fallback."""
        if LLM_AVAILABLE:
            return self._enhance_with_llm(original_bullet, target_skill, job_context)
        else:
            return self._enhance_with_rules(original_bullet, target_skill)

    def _enhance_with_llm(
        self,
        original: str,
        target_skill: str | None,
        job_context: str | None,
    ) -> STAREnhancementResult:
        """Call Gemini API with structured STAR prompt."""
        try:
            import google.generativeai as genai

            from backend.config.settings import settings

            prompt = f"""You are an elite executive resume writer and ATS optimization expert.
Rewrite the following resume bullet point using the STAR \
(Situation, Task, Action, Result) methodology.
Ensure it begins with a high-impact action verb and includes \
quantifiable metrics (e.g. percentages, latency improvements, scale).

Original Bullet: "{original}"
Target Skill to Incorporate: "{target_skill or 'None'}"
Job Context: "{job_context or 'Software Engineering'}"

Return ONLY a valid JSON object matching this schema:
{{
    "star_bullet": "High-impact STAR formatted bullet point",
    "quantified_metric_added": true,
    "changes_made": ["Action verb updated", "Quantified metric added"]
}}
"""
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(settings.gemini_model)
            response = model.generate_content(prompt)

            content = response.text
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return STAREnhancementResult(
                    original_bullet=original,
                    star_bullet=data.get("star_bullet", original),
                    target_skill_added=target_skill,
                    quantified_metric_added=data.get("quantified_metric_added", True),
                    changes_made=data.get("changes_made", ["Formatted with STAR methodology"]),
                )
        except Exception as e:
            logger.error("LLM STAR enhancement failed: %s", str(e))

        return self._enhance_with_rules(original, target_skill)

    def _enhance_with_rules(self, original: str, target_skill: str | None) -> STAREnhancementResult:
        """Fallback STAR rule enhancement."""
        improved = original.strip()
        changes = []

        # Ensure strong verb start
        verbs = ["Engineered", "Spearheaded", "Orchestrated", "Overhauled", "Automated"]
        words = improved.split()
        if words:
            verb = verbs[len(original) % len(verbs)]
            first_word_lower = words[0].lower()
            if first_word_lower in {
                "selected", "worked", "helped",
                "assisted", "responsible", "handled",
            }:
                improved = f"{verb} {words[0].lower()} {' '.join(words[1:])}"
                changes.append("Transformed leading verb to high-impact action verb.")
            elif first_word_lower not in {
                "engineered", "spearheaded", "orchestrated",
                "overhauled", "automated", "built", "developed",
            }:
                improved = f"{verb} {' '.join(words)}"
                changes.append("Added high-impact action verb.")

        if target_skill and target_skill.lower() not in original.lower():
            improved += f" using {target_skill}."
            changes.append(f"Incorporated target skill: {target_skill}.")

        return STAREnhancementResult(
            original_bullet=original,
            star_bullet=improved,
            target_skill_added=target_skill,
            quantified_metric_added=False,
            changes_made=changes,
        )

