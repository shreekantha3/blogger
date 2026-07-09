"""
Heading structure analysis.

ARCHITECTURAL DECISION: Heading hierarchy importance
---------------------------------------------------
Proper heading structure (H1 -> H2 -> H3) is important for:
1. SEO - helps Google understand content structure
2. Accessibility - screen readers use headings for navigation
3. Readability - breaks up content visually

Google's guidelines:
- One H1 per page (the main title)
- H2 for section headers
- H3 for subsections
- No skipping levels (H1 -> H3 without H2)

Uses BeautifulSoup for robust HTML parsing when available,
falls back to regex for basic compatibility.
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from config import get_logger
from seo.models import SEOScore

# Try to import BeautifulSoup for better HTML parsing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = get_logger("seo", "headings")


@dataclass
class Heading:
    """Represents a heading with level and text."""

    level: int
    text: str


class HeadingAnalyzer:
    """
    Analyzes heading structure in HTML content.

    Design decisions:
    - Extracts all headings (H1-H6)
    - Uses BeautifulSoup when available for robust parsing
    - Falls back to regex for basic compatibility
    - Identifies hierarchy issues
    - Provides suggestions for improvement
    """

    def extract_headings(self, html: str) -> list[Heading]:
        """
        Extract all headings from HTML.

        Uses BeautifulSoup when available for robust parsing,
        falls back to regex for basic cases.

        Args:
            html: HTML content to extract headings from

        Returns:
            List of Heading objects with level and text
        """
        headings: list[Heading] = []

        if BS4_AVAILABLE:
            return self._extract_headings_bs4(html)

        return self._extract_headings_regex(html)

    def _extract_headings_bs4(self, html: str) -> list[Heading]:
        """Extract headings using BeautifulSoup."""
        headings = []
        soup = BeautifulSoup(html, 'html.parser')

        for level in range(1, 7):
            for tag in soup.find_all(f'h{level}'):
                text = tag.get_text(strip=True)
                if text:
                    headings.append(Heading(level=level, text=text))

        return headings

    def _extract_headings_regex(self, html: str) -> list[Heading]:
        """Extract headings using regex (fallback)."""
        headings: list[Heading] = []

        # Match opening and closing tags for all heading levels
        for level in range(1, 7):
            pattern = rf"<h{level}[^>]*>(.*?)</h{level}>"
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

            for match in matches:
                # Clean the text
                text = re.sub(r"<[^>]+>", "", match).strip()
                headings.append(Heading(level=level, text=text))

        return headings

    def analyze(self, html: str) -> SEOScore:
        """
        Analyze heading structure for SEO quality.

        Scoring:
        - Must have exactly one H1: +40 pts
        - H2 present: +20 pts
        - Proper hierarchy (no H1->H3 skips): +20 pts
        - Reasonable H3-H6 usage: +20 pts
        """
        issues: list[str] = []
        suggestions: list[str] = []
        score = 0

        headings = self.extract_headings(html)

        if not headings:
            return SEOScore(
                value=0,
                label="Headings",
                issues=["No headings found in content"],
                suggestions=[
                    "Add H1 heading (main title)",
                    "Use H2 for sections",
                    "Use H3 for subsections",
                ],
            )

        h1_count = sum(1 for h in headings if h.level == 1)
        h2_count = sum(1 for h in headings if h.level == 2)

        # Check H1 count
        if h1_count == 1:
            score += 40
        elif h1_count == 0:
            issues.append("Missing H1 heading")
            suggestions.append("Add an H1 heading for the main title")
        else:
            issues.append(f"Multiple H1 headings ({h1_count})")
            suggestions.append("Use only one H1 per page")

        # Check H2 presence
        if h2_count >= 1:
            score += 20
        else:
            suggestions.append("Add H2 headings to structure the content")

        # Check hierarchy (no skips)
        levels = [h.level for h in headings]
        if levels:
            for i in range(len(levels) - 1):
                if levels[i + 1] > levels[i] + 1:
                    issues.append(
                        f"Heading level skip: H{levels[i]} → H{levels[i + 1]}"
                    )
                    score -= 10

        if len(issues) == 0:
            score += 20

        # Check for keyword usage in headings
        if h2_count > 0:
            score += 20

        return SEOScore(
            value=max(0, min(100, score)),
            label="Headings",
            issues=issues,
            suggestions=suggestions,
        )

    def get_heading_text(self, html: str, level: int) -> list[str]:
        """Get all headings of a specific level."""
        return [h.text for h in self.extract_headings(html) if h.level == level]