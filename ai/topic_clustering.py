"""
Topic clustering for topical authority and internal linking.

ARCHITECTURAL DECISION: Topic Clustering Strategy
-------------------------------------------------
Based on Honest Code Review: "Internal linking should be graph-based,
not heuristic - better topical clusters."

This module:
1. Groups posts by topic similarity
2. Identifies pillar content opportunities
3. Suggests cluster content gaps
4. Improves internal link relevance
"""

from dataclasses import dataclass, field
from typing import Optional
import re

from config import get_logger
from ai.models import BlogPost

logger = get_logger("ai", "clustering")


@dataclass
class TopicCluster:
    """A cluster of related topics."""

    main_topic: str
    related_posts: list[str] = field(default_factory=list)  # post_ids
    keywords: list[str] = field(default_factory=list)
    pillar_page: Optional[str] = None  # main post_id for this topic
    suggested_content: list[str] = field(default_factory=list)


class TopicClusterer:
    """
    Cluster content by topic for topical authority.

    Usage:
        clusterer = TopicClusterer()
        clusters = clusterer.cluster_posts(all_posts)
        print(f"Found {len(clusters)} topic clusters")
    """

    def __init__(self) -> None:
        """Initialize clusterer."""
        pass

    def cluster_posts(
        self,
        posts: list[BlogPost],
    ) -> list[TopicCluster]:
        """
        Cluster posts by topic similarity.

        Args:
            posts: All blog posts

        Returns:
            List of TopicCluster objects
        """
        # Extract keywords from each post
        post_keywords: dict[str, set[str]] = {}
        for post in posts:
            key_set = set(getattr(post, 'labels', []) or [])
            key_set.add(getattr(post, 'title', '').split()[0].lower())
            post_keywords[post.post_id if hasattr(post, 'post_id') else post.title] = key_set

        # Find common themes
        clusters = self._find_clusters(post_keywords)

        logger.info("Created topic clusters", count=len(clusters))

        return clusters

    def _find_clusters(self, post_keywords: dict[str, set[str]]) -> list[TopicCluster]:
        """Find topic clusters from keyword overlap."""
        clusters = []
        visited = set()

        for post_id, keywords in post_keywords.items():
            if post_id in visited:
                continue

            # Find posts with overlapping keywords
            cluster_posts = [post_id]
            cluster_keywords = set(keywords)

            for other_id, other_kw in post_keywords.items():
                if other_id in visited or other_id == post_id:
                    continue

                overlap = len(keywords & other_kw)
                if overlap >= 1:  # At least 1 shared keyword
                    cluster_posts.append(other_id)
                    cluster_keywords.update(other_kw)

            if len(cluster_posts) > 1:
                visited.update(cluster_posts)
                main_topic = self._extract_main_topic(cluster_posts)

                clusters.append(TopicCluster(
                    main_topic=main_topic,
                    related_posts=cluster_posts,
                    keywords=list(cluster_keywords),
                    pillar_page=cluster_posts[0],
                    suggested_content=self._suggest_cluster_content(keywords),
                ))

        return clusters

    def _extract_main_topic(self, post_ids: list[str]) -> str:
        """Extract main topic from cluster."""
        # Look for common terms in titles
        all_text = " ".join(post_ids).lower()
        # Find recruitment-related terms
        recruitment_terms = ["ksp", "excise", "recruitment", "recruit"]
        for term in recruitment_terms:
            if term in all_text:
                return f"{term.title()} Recruitment"
        return "General"

    def _suggest_cluster_content(self, keywords: set[str]) -> list[str]:
        """Suggest content to fill cluster gaps."""
        suggestions = []

        # For recruitment clusters
        if "recruitment" in " ".join(keywords).lower():
            suggestions.extend([
                "Application Process Guide",
                "Eligibility Criteria Deep Dive",
                "Salary and Benefits Analysis",
                "Preparation Tips and Tricks",
                "Common Mistakes to Avoid",
            ])

        return suggestions

    def get_cluster_suggestions(
        self,
        topic: str,
        existing_posts: list[BlogPost],
    ) -> dict:
        """
        Get suggestions for expanding a topic cluster.

        Args:
            topic: Main topic to expand
            existing_posts: Posts to analyze

        Returns:
            Suggestions for cluster expansion
        """
        clusters = self.cluster_posts(existing_posts)

        for cluster in clusters:
            if topic.lower() in cluster.main_topic.lower():
                return {
                    "topic": cluster.main_topic,
                    "existing_posts": cluster.related_posts,
                    "suggested_content": cluster.suggested_content,
                    "keywords_to_use": cluster.keywords[:10],
                }

        return {
            "topic": topic,
            "existing_posts": [],
            "suggested_content": ["Create pillar page", "Add supporting guides"],
        }


# Convenience function for CLI
def cluster_articles(posts_dir: Optional[str] = None) -> list[TopicCluster]:
    """
    Cluster all articles in directory.

    Args:
        posts_dir: Directory containing articles

    Returns:
        Topic clusters
    """
    # Would integrate with actual post loading
    return []