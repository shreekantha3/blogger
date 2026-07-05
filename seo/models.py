"""
SEO data models.

ARCHITECTURAL DECISION: Result models
--------------------------------------
We use specific result models to provide structured feedback.
This allows the web dashboard (Phase 7) to display:
- Scores (0-100 scale)
- Issues (list of problems)
- Suggestions (actionable fixes)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SEOScore:
    """
    SEO score for a specific metric (0-100).

    Attributes:
        value: Numeric score
        max_value: Maximum possible (usually 100)
        label: Human-readable label
        issues: List of identified issues
        suggestions: List of suggested fixes
    """

    value: int
    max_value: int = 100
    label: str = ""
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        """Get score as percentage."""
        return (self.value / self.max_value) * 100 if self.max_value > 0 else 0


@dataclass
class SEORport:
    """
    Comprehensive SEO report for a blog post.

    This aggregates all individual analyzer results into one report.
    """

    title_score: SEOScore
    meta_score: SEOScore
    heading_score: SEOScore
    keyword_score: SEOScore
    readability_score: SEOScore

    @property
    def overall_score(self) -> int:
        """Calculate overall SEO score."""
        total = (
            self.title_score.value
            + self.meta_score.value
            + self.heading_score.value
            + self.keyword_score.value
            + self.readability_score.value
        )
        return int(total / 5)

    @property
    def all_issues(self) -> list[str]:
        """Get all issues from all analyzers."""
        issues = []
        for score in [
            self.title_score,
            self.meta_score,
            self.heading_score,
            self.keyword_score,
            self.readability_score,
        ]:
            issues.extend(score.issues)
        return issues

    @property
    def all_suggestions(self) -> list[str]:
        """Get all suggestions from all analyzers."""
        suggestions = []
        for score in [
            self.title_score,
            self.meta_score,
            self.heading_score,
            self.keyword_score,
            self.readability_score,
        ]:
            suggestions.extend(score.suggestions)
        return suggestions

    def is_seo_optimal(self, threshold: int = 80) -> bool:
        """Check if overall score meets threshold."""
        return self.overall_score >= threshold