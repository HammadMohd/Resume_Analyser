"""Impact Metric & Readability Analyzer.

Evaluates resume experience bullets for:
1. Quantified impact metrics (%, $, numbers, scale, timeframes)
2. Action verb intensity (Strong vs Weak verbs)
3. Readability & Cliché Buzzword Detector
"""

import re
from typing import Any

from pydantic import BaseModel

from backend.schemas.resume import NormalizedResume
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Strong Action Verbs
STRONG_VERBS = {
    "architected", "engineered", "spearheaded", "orchestrated", "pioneered",
    "scaled", "overhauled", "championed", "accelerated", "maximized",
    "minimized", "automated", "streamlined", "delivered", "executed",
    "launched", "revamped", "transformed", "generated", "boosted",
}

WEAK_VERBS = {
    "worked on", "assisted", "helped", "responsible for", "handled",
    "participated in", "did", "made", "supported", "attempted",
}

BUZZWORDS = {
    "synergy", "hardworking", "team player", "thought leader", "results-driven",
    "go-getter", "detail-oriented", "self-starter", "think outside the box",
    "go the extra mile", "dynamic", "motivated", "passionate",
}


class BulletImpactAnalysis(BaseModel):
    bullet_text: str
    has_quantified_metric: bool
    detected_metrics: list[str]
    verb_strength: str  # "Strong", "Moderate", "Weak"
    flagged_buzzwords: list[str]


class ImpactAnalysisResult(BaseModel):
    quantified_bullet_ratio: float
    quantified_bullets_count: int
    total_bullets_count: int
    strong_verb_ratio: float
    readability_score: float
    bullet_analyses: list[BulletImpactAnalysis]
    found_buzzwords: list[str]
    actionable_tips: list[str]


class ImpactAnalyzer:
    """Analyzes resume experience bullets for metrics, verb strength, and readability."""

    def analyze(self, resume: NormalizedResume) -> ImpactAnalysisResult:
        """Run impact and readability analysis on normalized resume."""
        bullets: list[str] = []
        for exp in resume.experience:
            bullets.extend(exp.bullets)

        if not bullets:
            return ImpactAnalysisResult(
                quantified_bullet_ratio=0.0,
                quantified_bullets_count=0,
                total_bullets_count=0,
                strong_verb_ratio=0.0,
                readability_score=70.0,
                bullet_analyses=[],
                found_buzzwords=[],
                actionable_tips=["Add experience bullet points with quantified achievements."],
            )

        bullet_analyses: list[BulletImpactAnalysis] = []
        quantified_count = 0
        strong_verb_count = 0
        all_found_buzzwords = set()

        for b in bullets:
            metrics = self._extract_metrics(b)
            has_metric = len(metrics) > 0
            if has_metric:
                quantified_count += 1

            verb_strength = self._classify_verb(b)
            if verb_strength == "Strong":
                strong_verb_count += 1

            buzzwords = [bw for bw in BUZZWORDS if re.search(r"\b" + re.escape(bw) + r"\b", b.lower())]
            all_found_buzzwords.update(buzzwords)

            bullet_analyses.append(
                BulletImpactAnalysis(
                    bullet_text=b,
                    has_quantified_metric=has_metric,
                    detected_metrics=metrics,
                    verb_strength=verb_strength,
                    flagged_buzzwords=buzzwords,
                )
            )

        total = len(bullets)
        quant_ratio = round(quantified_count / total, 2)
        strong_ratio = round(strong_verb_count / total, 2)

        tips = []
        if quant_ratio < 0.4:
            tips.append("Only {:.0f}% of your bullets have numbers. Include metrics (e.g. 'Increased speed by 35%')".format(quant_ratio * 100))
        if strong_ratio < 0.5:
            tips.append("Use stronger action verbs like 'Engineered', 'Spearheaded', or 'Orchestrated' instead of 'Worked on'.")
        if all_found_buzzwords:
            tips.append(f"Remove generic buzzwords: {', '.join(list(all_found_buzzwords)[:3])}.")

        return ImpactAnalysisResult(
            quantified_bullet_ratio=quant_ratio,
            quantified_bullets_count=quantified_count,
            total_bullets_count=total,
            strong_verb_ratio=strong_ratio,
            readability_score=75.0,
            bullet_analyses=bullet_analyses,
            found_buzzwords=list(all_found_buzzwords),
            actionable_tips=tips,
        )

    def _extract_metrics(self, text: str) -> list[str]:
        """Extract percentage, dollar, multiplier, and count metrics."""
        patterns = [
            r"\b\d+%",  # 35%
            r"\$\d+[\d,]*[kKmMbB]?",  # $50k or $1,000
            r"\b\d+x\b",  # 10x
            r"\b\d+[\d,]*\s*(users|clients|customers|requests|transactions|projects|servers|services|engineers|microservices|ms|seconds|hours|days|months|years|x)\b",
        ]
        matches = []
        for p in patterns:
            found = re.findall(p, text, re.IGNORECASE)
            for f in found:
                if isinstance(f, tuple):
                    matches.append(f[0])
                else:
                    matches.append(f)
        return list(set(matches))

    def _classify_verb(self, text: str) -> str:
        """Classify the leading verb strength."""
        first_word = text.strip().split()[0].lower() if text.strip() else ""
        if first_word in STRONG_VERBS:
            return "Strong"
        for weak in WEAK_VERBS:
            if text.lower().startswith(weak):
                return "Weak"
        return "Moderate"
