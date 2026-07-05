"""
Internal Linking Suggestions Module.

ARCHITECTURAL DECISION: Link Genius Implementation
---------------------------------------------------
This module implements Link Genius functionality for:
1. Finding related posts based on content similarity
2. Generating keyword-rich anchor text
3. Suggesting 3-5 internal links per 1000 words

Based on RankMath SEO guidelines: 3-5 internal links per 1,000 words
with keyword-rich anchor text for better SEO.

Usage:
    from ai.internal_linking import InternalLinkSuggester

    suggester = InternalLinkSuggester()
    links = suggester.find_related_posts(
        current_content="Article content...",
        target_keywords=["python", "seo"],
        existing_posts=[
            {"id": "123", "title": "Python Basics", "content": "...", "url": "/python-basics", "keywords": ["python", "beginner"]},
            {"id": "456", "title": "SEO Tips", "content": "...", "url": "/seo-tips", "keywords": ["seo", "optimization"]},
        ]
    )
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class InternalLink:
    """Represents an internal link suggestion."""
    post_id: str
    post_title: str
    url: str
    anchor_text: str
    relevance_score: float
    reason: str


class InternalLinkSuggester:
    """
    Finds related posts and generates internal link suggestions.

    Implements Link Genius functionality for SEO optimization.
    """

    def __init__(self, min_links_per_1000_words: int = 3, max_links_per_1000_words: int = 5):
        """
        Initialize the link suggester.

        Args:
            min_links_per_1000_words: Minimum links to suggest
            max_links_per_1000_words: Maximum links to suggest
        """
        self.min_links = min_links_per_1000_words
        self.max_links = max_links_per_1000_words

    def find_related_posts(
        self,
        current_content: str,
        target_keywords: Optional[List[str]] = None,
        existing_posts: Optional[List[Dict[str, Any]]] = None,
        max_suggestions: int = 5,
    ) -> List[InternalLink]:
        """
        Find related posts and generate link suggestions.

        Args:
            current_content: HTML content of the current article
            target_keywords: Primary keywords for the current article
            existing_posts: List of existing posts with id, title, content, url, keywords
            max_suggestions: Maximum number of links to suggest

        Returns:
            List of InternalLink objects with anchor text and relevance scores

        Example:
            >>> posts = [{"id": "1", "title": "Python Guide", "content": "...", "url": "/python", "keywords": ["python"]}]
            >>> links = suggester.find_related_posts(content, ["python"], posts)
        """
        if not existing_posts:
            return []

        # Extract keywords from content if not provided
        if not target_keywords:
            target_keywords = self._extract_keywords(current_content)

        # Calculate word count for link density
        word_count = len(re.sub(r'<[^>]+>', '', current_content).split())
        target_link_count = min(
            max(self.min_links, (word_count // 1000) * self.min_links),
            max(self.max_links, (word_count // 1000) * self.max_links)
        )

        # Score each post for relevance
        scored_posts = []
        for post in existing_posts:
            score = self._calculate_relevance(
                current_keywords=target_keywords,
                post_keywords=post.get("keywords", []),
                post_title=post.get("title", ""),
                current_content=current_content,
                post_content=post.get("content", ""),
            )

            if score > 0:
                scored_posts.append((post, score))

        # Sort by relevance score
        scored_posts.sort(key=lambda x: x[1], reverse=True)

        # Generate link suggestions
        links = []
        for post, score in scored_posts[:target_link_count]:
            anchor_text = self._generate_anchor_text(
                post_title=post.get("title", ""),
                post_keywords=post.get("keywords", []),
                current_keywords=target_keywords,
            )

            link = InternalLink(
                post_id=post.get("id", ""),
                post_title=post.get("title", ""),
                url=post.get("url", ""),
                anchor_text=anchor_text,
                relevance_score=score,
                reason=self._get_link_reason(score),
            )
            links.append(link)

        return links

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content for matching."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'\s+', ' ', text).lower()

        # Extract words (simple approach - could be enhanced with NLP)
        words = re.findall(r'[a-z]{4,}', text)

        # Count word frequency
        word_count: Dict[str, int] = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1

        # Return top keywords
        sorted_keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_keywords[:10]]

    def _calculate_relevance(
        self,
        current_keywords: List[str],
        post_keywords: List[str],
        post_title: str,
        current_content: str,
        post_content: str,
    ) -> float:
        """Calculate relevance score between current article and a post."""
        if not post_keywords and not current_keywords:
            return 0.0

        score = 0.0

        # Keyword overlap
        current_set = set(k.lower() for k in current_keywords)
        post_set = set(k.lower() for k in post_keywords)

        if current_set and post_set:
            overlap = len(current_set & post_set)
            score += overlap * 0.3

        # Title keyword matching
        title_score = sum(1 for kw in current_keywords if kw.lower() in post_title.lower())
        score += title_score * 0.2

        # Content similarity (simple word overlap)
        current_words = set(re.findall(r'\w+', current_content.lower()))
        post_words = set(re.findall(r'\w+', post_content.lower()))

        if current_words and post_words:
            content_overlap = len(current_words & post_words) / len(current_words | post_words)
            score += content_overlap * 0.3

        # Boost for exact keyword matches
        exact_matches = sum(1 for kw in current_keywords 
                          if kw.lower() in post_content.lower())
        score += exact_matches * 0.1

        return min(1.0, score)

    def _generate_anchor_text(
        self,
        post_title: str,
        post_keywords: List[str],
        current_keywords: List[str],
    ) -> str:
        """Generate keyword-rich anchor text for the link."""
        # Find matching keywords
        post_kw_set = set(k.lower() for k in post_keywords)
        current_kw_set = set(k.lower() for k in current_keywords)
        matching_kw = list(post_kw_set & current_kw_set)

        if matching_kw:
            # Use the matching keyword as anchor text
            return matching_kw[0].title()

        # Otherwise, use a descriptive title
        # Clean the title (remove common words)
        clean_title = re.sub(r'^(the|a|an)\s+', '', post_title, flags=re.IGNORECASE)
        clean_title = re.sub(r'\s*[:]\s*.*$', '', clean_title)  # Remove trailing subtitles

        return clean_title[:60]  # Keep anchor text reasonable length

    def _get_link_reason(self, score: float) -> str:
        """Get human-readable reason for the link suggestion."""
        if score >= 0.8:
            return "Highly relevant - exact keyword match and content overlap"
        elif score >= 0.6:
            return "Relevant - related topic with keyword overlap"
        elif score >= 0.4:
            return "Moderately relevant - some topic overlap"
        else:
            return "Related content - contextual link opportunity"

    def format_links_html(self, links: List[InternalLink]) -> str:
        """
        Format link suggestions as HTML.

        Args:
            links: List of InternalLink objects

        Returns:
            HTML string with formatted links
        """
        if not links:
            return ""

        html_parts = ["<h2>Further Reading</h2>"]
        for link in links:
            html_parts.append(
                f'<p><a href="{link.url}">{link.anchor_text}</a>: {link.post_title}</p>'
            )

        return "".join(html_parts)

    def get_link_density_recommendation(self, word_count: int) -> Dict[str, int]:
        """
        Get recommended link count based on word count.

        Args:
            word_count: Total word count of the article

        Returns:
            Dict with min_links, max_links, and recommended
        """
        links_per_1000 = word_count / 1000

        return {
            "min_links": max(1, int(links_per_1000 * 3)),
            "max_links": max(2, int(links_per_1000 * 5)),
            "recommended": max(3, int(links_per_1000 * 4)),
        }
