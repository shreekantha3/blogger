"""
Keyword density analysis.

ARCHITECTURAL DECISION: Keyword vs Semantic analysis
----------------------------------------------------
This analyzer focuses on keyword density because:
1. It's measurable and actionable
2. It catches over-optimization (keyword stuffing)
3. It ensures target keywords appear

Google's keyword density guidelines:
- Target: 0.5-2% of total word count
- Avoid: Exact match repetition
- Focus: Natural language and semantic variants
"""

import re
from typing import Optional

from config import get_logger
from seo.models import SEOScore
from utils.helpers import extract_text_from_html

logger = get_logger("seo", "keywords")

# Common stop words to filter out
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
}


class KeywordAnalyzer:
    """
    Analyzes keyword density and distribution.

    Design decisions:
    - Calculates density for provided target keywords
    - Identifies potential keyword stuffing
    - Suggests optimal placement (first 100 words, headings)
    """

    OPTIMAL_MIN_DENSITY = 0.005  # 0.5%
    OPTIMAL_MAX_DENSITY = 0.02   # 2%
    WARNING_MAX_DENSITY = 0.03   # 3% (potential stuffing)

    def analyze(
        self,
        content: str,
        target_keyword: Optional[str] = None,
    ) -> SEOScore:
        """
        Analyze keyword density for content.

        Args:
            content: HTML content to analyze
            target_keyword: Optional primary keyword to check

        Returns:
            SEOScore with keyword analysis results
        """
        issues: list[str] = []
        suggestions: list[str] = []
        score = 100

        # Extract text and calculate word count
        text = extract_text_from_html(content)
        words = [w.lower() for w in re.findall(r"\b\w+\b", text)]
        total_words = len(words)

        if total_words == 0:
            return SEOScore(
                value=0,
                label="Keywords",
                issues=["No words found in content"],
                suggestions=["Add substantive content"],
            )

        # Filter out stop words for analysis
        content_words = [w for w in words if w not in STOP_WORDS]

        if target_keyword:
            # Check target keyword density
            density = self._calculate_density(content, target_keyword)

            if density < self.OPTIMAL_MIN_DENSITY:
                suggestions.append(
                    f"Consider using target keyword '{target_keyword}' more often"
                )
                score -= 20
            elif density > self.WARNING_MAX_DENSITY:
                issues.append(
                    f"Keyword '{target_keyword}' may be overused "
                    f"({density * 100:.1f}% density)"
                )
                score -= 30

        # Check for keyword stuffing (only flag if it appears many times)
        word_freq = self._get_word_frequency(content_words)
        for word, count in word_freq.items():
            if count > 5 and count / total_words > self.WARNING_MAX_DENSITY:
                issues.append(f"Word '{word}' may be overused ({count} times)")
                score -= 10

        # Deduplicate
        suggestions = list(set(suggestions))

        return SEOScore(
            value=max(0, score),
            label="Keywords",
            issues=issues,
            suggestions=suggestions,
        )

    def _calculate_density(self, content: str, keyword: str) -> float:
        """Calculate keyword density (occurrences / total words)."""
        text = extract_text_from_html(content)
        words = re.findall(r"\b\w+\b", text.lower())
        total_words = len(words)

        if total_words == 0:
            return 0.0

        keyword_lower = keyword.lower()
        occurrences = sum(1 for w in words if w == keyword_lower)

        return occurrences / total_words

    def _get_word_frequency(self, words: list[str]) -> dict[str, int]:
        """Get word frequency count."""
        from collections import Counter
        return dict(Counter(words).most_common(20))

    def suggest_keywords(
        self,
        content: str,
        max_suggestions: int = 10,
    ) -> list[str]:
        """
        Suggest potential keywords based on content.

        Returns top N non-stop words by frequency.
        """
        text = extract_text_from_html(content)
        words = [w.lower() for w in re.findall(r"\b\w+\b", text)]

        # Filter and sort
        content_words = [w for w in words if w not in STOP_WORDS and len(w) > 3]

        from collections import Counter
        freq = Counter(content_words)

        return [word for word, _ in freq.most_common(max_suggestions)]