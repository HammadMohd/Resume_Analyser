"""Rule engine — coordinates all rule evaluations.

This module runs all rule categories against a resume and
combines results into a comprehensive evaluation.

Responsibilities:
    - Running all rule categories
    - Combining scores with weights
    - Aggregating all issues
    - Calculating overall grade

NOT responsible for:
    - Individual rule logic (belongs to respective rule modules)
    - Resume parsing or extraction (belongs to parser module)
"""

import time

from backend.rules.bullet_rules import evaluate_bullets
from backend.rules.completeness_rules import evaluate_completeness
from backend.rules.contact_rules import evaluate_contact
from backend.rules.section_rules import evaluate_sections
from backend.schemas.resume import NormalizedResume
from backend.schemas.rules import Issue, RuleResult
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class RuleEngine:
    """Evaluate resume against ATS rules."""

    def evaluate(self, resume: NormalizedResume) -> RuleResult:
        """Run all rules against the resume.

        Args:
            resume: Normalized resume data.

        Returns:
            RuleResult with scores, issues, and grade.
        """
        start = time.time()

        # Run each rule category
        contact_result = evaluate_contact(resume.contact)
        section_result = evaluate_sections(resume)
        bullet_result = evaluate_bullets(resume)

        category_results = [contact_result, section_result, bullet_result]

        # Run completeness (needs all other results)
        completeness_result = evaluate_completeness(resume, category_results)
        category_results.append(completeness_result)

        # Calculate weighted overall score
        overall_score = self._calculate_overall_score(category_results)
        overall_grade = self._calculate_grade(overall_score)

        # Aggregate all issues
        all_issues: list[Issue] = []
        total_passed = 0
        total_checks = 0

        for result in category_results:
            all_issues.extend(result.issues)
            total_passed += result.checks_passed
            total_checks += result.checks_total

        elapsed = (time.time() - start) * 1000

        logger.info(
            "Rule evaluation completed: %.0f/100 (Grade: %s) in %.2f ms",
            overall_score,
            overall_grade,
            elapsed,
        )

        return RuleResult(
            filename=resume.filename,
            overall_score=overall_score,
            overall_grade=overall_grade,
            categories=category_results,
            all_issues=all_issues,
            total_checks_passed=total_passed,
            total_checks=total_checks,
            evaluation_time_ms=round(elapsed, 2),
        )

    def _calculate_overall_score(self, categories: list) -> float:
        """Calculate weighted overall score from categories."""
        weights = {
            "contact": 0.20,
            "sections": 0.30,
            "bullets": 0.35,
            "completeness": 0.15,
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for cat in categories:
            weight = weights.get(cat.category, 0)
            if weight > 0:
                weighted_sum += cat.score * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0

    def _calculate_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
