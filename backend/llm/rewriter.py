"""Bullet rewriter — orchestrates LLM-based bullet improvement.

This module coordinates prompt building, LLM calls, and output
validation to produce improved bullet points.

Supports two modes:
1. Full mode: Uses OpenAI API (requires API key)
2. Rule-based mode: Applies improvements without LLM (fallback)
"""

import json
import re

from backend.llm import LLM_AVAILABLE
from backend.llm.prompt_builder import build_bullet_rewrite_prompt
from backend.llm.schemas import (
    BulletRewriteRequest,
    BulletRewriteResponse,
    RewriteRequest,
    RewriteResponse,
)
from backend.llm.validator import validate_bullet_rewrite
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class BulletRewriter:
    """Rewrite bullet points using LLM or rule-based fallback."""

    def __init__(self) -> None:
        """Initialize rewriter."""
        self.use_llm = LLM_AVAILABLE

    def rewrite_bullet(self, request: BulletRewriteRequest) -> BulletRewriteResponse:
        """Rewrite a single bullet point.

        Args:
            request: Bullet rewrite request.

        Returns:
            Rewritten bullet with metadata.
        """
        if self.use_llm:
            return self._rewrite_with_llm(request)
        else:
            return self._rewrite_with_rules(request)

    def rewrite_bullets(self, request: RewriteRequest) -> RewriteResponse:
        """Rewrite multiple bullet points.

        Args:
            request: Multi-bullet rewrite request.

        Returns:
            Complete rewrite response with all bullets.
        """
        rewritten = []
        total_confidence = 0.0

        for bullet_req in request.bullets:
            # Add context from request
            if request.job_title and not bullet_req.context:
                bullet_req.context = request.job_title

            result = self.rewrite_bullet(bullet_req)
            rewritten.append(result)
            total_confidence += result.confidence

        avg_confidence = total_confidence / len(rewritten) if rewritten else 0
        total_improved = sum(1 for r in rewritten if r.confidence > 0.5)

        return RewriteResponse(
            rewritten_bullets=rewritten,
            total_improved=total_improved,
            overall_confidence=avg_confidence,
            validation_passed=True,
        )

    def _rewrite_with_llm(self, request: BulletRewriteRequest) -> BulletRewriteResponse:
        """Rewrite using OpenAI API."""
        try:
            import openai

            prompt = build_bullet_rewrite_prompt(
                original=request.original,
                context=request.context,
                missing_skills=request.missing_skills,
            )

            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # Validate
            validation = validate_bullet_rewrite(
                original=request.original,
                improved=result.get("improved", request.original),
            )

            return BulletRewriteResponse(
                original=request.original,
                improved=validation.improved_bullet,
                changes_made=result.get("changes_made", []),
                confidence=result.get("confidence", 0.5) if validation.is_valid else 0.2,
            )

        except Exception as e:
            logger.error("LLM rewrite failed: %s", str(e))
            return self._rewrite_with_rules(request)

    def _rewrite_with_rules(self, request: BulletRewriteRequest) -> BulletRewriteResponse:
        """Rule-based rewrite without LLM."""
        original = request.original
        improved = original
        changes = []

        # Ensure starts with action verb
        words = original.split()
        if words and words[0].lower() not in _ACTION_VERBS:
            # Try to find a suitable verb
            for verb in ["Implemented", "Developed", "Built", "Led", "Improved"]:
                if verb.lower() in original.lower():
                    improved = verb + " " + original.lower().split(verb.lower(), 1)[-1].strip()
                    changes.append("Started with action verb")
                    break

        # Ensure reasonable length
        if len(improved) > 200:
            improved = improved[:197] + "..."
            changes.append("Trimmed to appropriate length")

        confidence = 0.4 if changes else 0.3

        return BulletRewriteResponse(
            original=original,
            improved=improved,
            changes_made=changes,
            confidence=confidence,
        )


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
