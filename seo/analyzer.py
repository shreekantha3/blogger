"""
Main SEO analyzer that combines all individual checks.

ARCHITECTURAL DECISION: Composite Pattern
------------------------------------------
The SEOAnalyzer is a composite that:
1. Delegates to specialized analyzers
2. Aggregates their results
3. Provides a unified interface

This allows:
- Adding new analyzers without changing this class
- Running all checks with one method call
- Getting a comprehensive report
"""

from typing import Optional

from config import get_logger
from seo.models import SEORport, SEOScore
from seo.meta import MetaDescriptionGenerator
from seo.headings import HeadingAnalyzer
from seo.keywords import KeywordAnalyzer
from seo.readability import ReadabilityAnalyzer

logger = get_logger("seo", "analyzer")


class SEOAnalyzer:
    """
    Comprehensive SEO analyzer for blog posts.

    Usage:
        analyzer = SEOAnalyzer()
        report = analyzer.analyze(post)
        print(f"Overall SEO score: {report.overall_score}")
        for issue in report.all_issues:
            print(f"Issue: {issue}")
    """

    def __init__(
        self,
        meta_generator: Optional[MetaDescriptionGenerator] = None,
        heading_analyzer: Optional[HeadingAnalyzer] = None,
        keyword_analyzer: Optional[KeywordAnalyzer] = None,
        readability_analyzer: Optional[ReadabilityAnalyzer] = None,
    ) -> None:
        """
        Initialize with optional custom analyzers.

        This allows dependency injection for testing.
        """
        self._meta = meta_generator or MetaDescriptionGenerator()
        self._headings = heading_analyzer or HeadingAnalyzer()
        self._keywords = keyword_analyzer or KeywordAnalyzer()
        self._readability = readability_analyzer or ReadabilityAnalyzer()

    def analyze(
        self,
        title: str,
        content: str,
        meta_description: Optional[str] = None,
        target_keyword: Optional[str] = None,
    ) -> SEORport:
        """
        Run all SEO analyses on a post.

        Args:
            title: Post title
            content: HTML content
            meta_description: Optional meta description (will generate if None)
            target_keyword: Optional target keyword to check

        Returns:
            Complete SEO report
        """
        logger.info("Running SEO analysis", title=title[:50])

        # Generate meta if not provided
        if not meta_description and content:
            meta_description = self._meta.generate(content, title=title)

        # Run all analyzers
        title_score = self._analyze_title(title)
        meta_score = self._meta.validate(meta_description or "")
        heading_score = self._headings.analyze(content)
        keyword_score = self._keywords.analyze(content, target_keyword)
        readability_score = self._readability.analyze(content)

        report = SEORport(
            title_score=title_score,
            meta_score=meta_score,
            heading_score=heading_score,
            keyword_score=keyword_score,
            readability_score=readability_score,
        )

        logger.info(
            "SEO analysis complete",
            overall_score=report.overall_score,
            issues_count=len(report.all_issues),
        )

        return report

    def _analyze_title(self, title: str) -> SEOScore:
        """Analyze title for SEO quality."""
        issues: list[str] = []
        suggestions: list[str] = []
        score = 100

        if not title:
            return SEOScore(
                value=0,
                label="Title",
                issues=["Missing title"],
                suggestions=["Add a descriptive title"],
            )

        # Title length check
        length = len(title)

        if length < 30:
            issues.append(f"Title too short ({length} chars)")
            suggestions.append("Aim for 50-60 characters")
            score -= 30
        elif length > 70:
            issues.append(f"Title may be truncated ({length} chars)")
            suggestions.append("Keep under 70 characters")
            score -= 20

        # Keyword stuffing check
        words = title.split()
        unique_ratio = len(set(w.lower() for w in words)) / len(words) if words else 0

        if unique_ratio < 0.5:
            issues.append("Title has repeated words")
            score -= 20

        return SEOScore(
            value=max(0, score),
            label="Title",
            issues=issues,
            suggestions=suggestions,
        )

    def validate_and_correct(
        self,
        title: str,
        content: str,
        meta_description: Optional[str] = None,
    ) -> tuple[bool, list[str]]:
        """
        Validate SEO and return corrections needed.

        Returns:
            Tuple of (is_valid, list of corrections)
        """
        report = self.analyze(title, content, meta_description)
        corrections = report.all_issues + report.all_suggestions

        return report.is_seo_optimal(), corrections

    def get_suggestions(self, report: SEORport) -> list[str]:
        """Get actionable suggestions from a report."""
        return [
            s
            for score in [
                report.title_score,
                report.meta_score,
                report.heading_score,
                report.keyword_score,
                report.readability_score,
            ]
            for s in score.suggestions
        ]