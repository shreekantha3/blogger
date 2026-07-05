"""
Meta description generation and validation.

ARCHITECTURAL DECISION: Why meta descriptions matter
--------------------------------------------------
Meta descriptions are crucial for SEO because:
1. They appear in search results (the snippet under title)
2. They influence click-through rate
3. Google uses them for featured snippets

Best practices applied:
- 150-160 characters optimal length
- Unique per page
- Call-to-action language ("Learn about...", "Discover...")
"""

import re
from typing import Optional

from config import get_logger
from seo.models import SEOScore
from utils.helpers import extract_text_from_html, truncate_text

logger = get_logger("seo", "meta")


class MetaDescriptionGenerator:
    """
    Generates and validates meta descriptions.

    Design decisions:
    - Truncates to 160 chars (Google display limit)
    - Removes HTML tags automatically
    - Scores based on length and quality
    """

    OPTIMAL_MIN_LENGTH = 120
    OPTIMAL_MAX_LENGTH = 160
    MAX_LENGTH = 320  # Some SEO tools allow up to this

    def generate(
        self,
        content: str,
        title: Optional[str] = None,
        target_length: int = 155,
    ) -> str:
        """
        Generate a meta description from post content.

        Args:
            content: HTML content to extract from
            title: Optional title to include
            target_length: Target length in characters

        Returns:
            Generated meta description
        """
        # Extract plain text
        text = extract_text_from_html(content)

        # Clean up the text
        text = re.sub(r"\s+", " ", text).strip()

        # Remove sentences that are too long (usually lists/tables)
        sentences = text.split(". ")
        clean_sentences = [
            s
            for s in sentences
            if len(s) < 200  # Filter out paragraph-like content
        ]

        # Build description from first few sentences
        description = ". ".join(clean_sentences[:3])

        # Ensure it ends properly
        if description and not description.endswith("."):
            description += "."

        # Truncate to target length
        description = truncate_text(description, target_length)

        return description

    def validate(self, meta_description: str) -> SEOScore:
        """
        Validate a meta description for SEO quality.

        Scoring criteria:
        - Length (ideal: 120-160 chars)
        - Uniqueness (not same as title - checked separately)
        - No excessive punctuation or caps

        Returns:
            SEOScore with validation results
        """
        issues: list[str] = []
        suggestions: list[str] = []
        score = 100

        if not meta_description:
            return SEOScore(
                value=0,
                label="Meta Description",
                issues=["Missing meta description"],
                suggestions=["Add a meta description between 120-160 characters"],
            )

        length = len(meta_description)

        # Length scoring
        if length < 80:
            issues.append(f"Meta description too short ({length} chars)")
            score -= 40
        elif length < self.OPTIMAL_MIN_LENGTH:
            score -= 20
            suggestions.append(
                f"Consider expanding to {self.OPTIMAL_MIN_LENGTH}+ characters"
            )

        if length > self.OPTIMAL_MAX_LENGTH + 20:
            issues.append(f"Meta description may be truncated ({length} chars)")
            score -= 20

        if length > self.MAX_LENGTH:
            issues.append(f"Meta description too long ({length} chars)")
            score -= 40

        # Content quality checks
        if re.search(r"[!]{2,}", meta_description):
            issues.append("Excessive exclamation marks")
            score -= 10

        if re.search(r"\b(Buy Now|Click Here|Read More)\b", meta_description):
            suggestions.append(
                "Avoid generic CTAs - use descriptive, specific language"
            )
            score -= 5

        # Deduplicate suggestions
        suggestions = list(set(suggestions))

        return SEOScore(
            value=max(0, score),
            label="Meta Description",
            issues=issues,
            suggestions=suggestions,
        )

    def from_post(self, post_content: str, title: Optional[str] = None) -> str:
        """
        Convenience method: generate meta description from post content.
        """
        return self.generate(post_content, title=title)