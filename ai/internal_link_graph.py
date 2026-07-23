"""
Internal Link Graph with PageRank analysis.

ARCHITECTURAL DECISION: Graph-Based Internal Linking
----------------------------------------------------
Extends the existing TF-IDF similarity approach with:
1. Content graph (nodes = posts, edges = semantic links)
2. PageRank scores to identify authority hubs
3. Orphan page detection (no inbound links)
4. Link opportunity suggestions for better topical clusters

This addresses "Google has zero reason to rank YOU over official site"
by building site authority through strategic internal linking.
"""

from dataclasses import dataclass, field
from typing import Optional
import json

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from config import get_settings, get_logger
from ai.models import BlogPost

logger = get_logger("ai", "link_graph")


@dataclass
class LinkGraphStats:
    """Statistics about the link graph."""

    total_posts: int
    total_links: int
    orphan_pages: int
    authority_hubs: list[str] = field(default_factory=list)
    average_score: float = 0.0


class InternalLinkGraph:
    """
    Build and analyze content graph for internal linking.

    Usage:
        graph = InternalLinkGraph()
        stats = graph.build_graph(all_posts)
        suggestions = graph.suggest_links(new_post, existing_posts)
    """

    def __init__(self) -> None:
        """Initialize link graph analyzer."""
        self._settings = get_settings()
        self._graph = None

    def build_graph(self, posts: list[BlogPost]) -> LinkGraphStats:
        """
        Build content graph from posts.

        Args:
            posts: List of all blog posts

        Returns:
            LinkGraphStats with graph statistics
        """
        if not NETWORKX_AVAILABLE:
            logger.warning("networkx not installed - using basic linking")
            return LinkGraphStats(
                total_posts=len(posts),
                total_links=0,
                orphan_pages=0,
            )

        self._graph = nx.DiGraph()

        # Add all posts as nodes
        for post in posts:
            self._graph.add_node(
                post.title,
                post_id=post.post_id,
                url=post.url if hasattr(post, 'url') else "",
                keywords=post.labels if hasattr(post, 'labels') else [],
            )

        # Build edges based on keyword overlap
        for i, post_a in enumerate(posts):
            for post_b in posts[i + 1:]:
                overlap = self._keyword_overlap(post_a, post_b)
                if overlap > 0.3:  # Significant overlap
                    self._graph.add_edge(post_a.title, post_b.title, weight=overlap)

        # Calculate PageRank scores
        try:
            scores = nx.pagerank(self._graph)
            self._scores = scores
        except Exception:
            self._scores = {n: 1.0 / len(posts) for n in self._graph.nodes()}

        # Find orphan pages (no inbound links)
        orphans = [n for n in self._graph.nodes() if self._graph.in_degree(n) == 0]

        # Find authority hubs (high PageRank, many outbound links)
        hubs = [
            n for n in self._graph.nodes()
            if self._scores.get(n, 0) > 0.01 and self._graph.out_degree(n) > 2
        ]

        stats = LinkGraphStats(
            total_posts=len(posts),
            total_links=self._graph.number_of_edges(),
            orphan_pages=len(orphans),
            authority_hubs=hubs[:10],
            average_score=sum(scores.values()) / len(scores) if scores else 0,
        )

        logger.info(
            "Built link graph",
            posts=len(posts),
            edges=self._graph.number_of_edges(),
            orphans=len(orphans),
        )

        return stats

    def suggest_links(
        self,
        new_post: BlogPost,
        existing_posts: list[BlogPost],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Suggest internal links for a new post.

        Args:
            new_post: The post to link from
            existing_posts: All existing posts
            top_k: Maximum suggestions

        Returns:
            List of link suggestions with reasons
        """
        suggestions = []

        # Find posts that complement this one
        for existing in existing_posts:
            if existing.title == new_post.title:
                continue

            overlap = self._keyword_overlap(new_post, existing)
            need_link = self._needs_link_to(existing, new_post)

            if overlap > 0.2 or need_link:
                suggestion = {
                    "post_id": existing.post_id if hasattr(existing, 'post_id') else "",
                    "title": existing.title,
                    "url": existing.url if hasattr(existing, 'url') else "",
                    "anchor_text": self._generate_anchor(existing, new_post),
                    "score": overlap,
                    "reason": "complements" if overlap > 0.4 else "contextual",
                }
                suggestions.append(suggestion)

        # Sort by score
        suggestions.sort(key=lambda x: x["score"], reverse=True)

        return suggestions[:top_k]

    def find_orphan_pages(self, posts: list[BlogPost]) -> list[dict]:
        """
        Find posts with no internal links pointing to them.

        These are losing potential authority.

        Args:
            posts: All blog posts

        Returns:
            List of orphan page info
        """
        if not self._graph:
            self.build_graph(posts)

        orphans = []
        for node in self._graph.nodes():
            if self._graph.in_degree(node) == 0:
                orphans.append({
                    "title": node,
                    "inbound_links": 0,
                    "suggested_parents": self._suggest_parents(
                        node, list(self._graph.nodes())
                    ),
                })

        return orphans

    def _keyword_overlap(self, post_a: BlogPost, post_b: BlogPost) -> float:
        """Calculate keyword overlap between two posts."""
        labels_a = set(
            getattr(post_a, 'labels', []) +
            getattr(post_a, 'keywords', []) +
            ([post_a.title] if hasattr(post_a, 'title') else [])
        )
        labels_b = set(
            getattr(post_b, 'labels', []) +
            getattr(post_b, 'keywords', []) +
            ([post_b.title] if hasattr(post_b, 'title') else [])
        )

        if not labels_a or not labels_b:
            return 0.0

        overlap = len(labels_a & labels_b)
        total = len(labels_a | labels_b)

        return overlap / total if total > 0 else 0.0

    def _needs_link_to(self, from_post: BlogPost, to_post: BlogPost) -> bool:
        """Check if a post needs a link to another for topical relevance."""
        # Posts without outbound links might need them
        score = self._scores.get(from_post.title, 0) if self._scores else 0
        return score < 0.02  # Low authority posts can benefit from linking

    def _generate_anchor(self, target: BlogPost, source: BlogPost) -> str:
        """Generate anchor text for a link."""
        # Use title-based anchor
        title = getattr(target, 'title', '')
        # Clean up
        clean = title.replace("2026", "").replace("Recruitment", "").strip()
        if len(clean) > 3 and clean != title:
            return clean + " guide"

        return title.split()[0] if title else "Read more"

    def _suggest_parents(self, topic: str, all_topics: list[str]) -> list[str]:
        """Suggest parent pages for orphan topics."""
        # Find similar topics
        suggestions = []
        for other in all_topics:
            if other == topic:
                continue
            # Simple word overlap
            words_topic = set(topic.lower().split())
            words_other = set(other.lower().split())
            overlap = len(words_topic & words_other) / len(words_topic)
            if overlap > 0.3:
                suggestions.append(other)

        return suggestions[:3]


# Convenience function for CLI
def analyze_internal_links(posts_json: Optional[str] = None):
    """
    Analyze internal linking for a list of posts.

    Args:
        posts_json: JSON array of posts with title, labels, content
    """
    if posts_json:
        try:
            data = json.loads(posts_json)
            posts = [BlogPost(**p) for p in data]
        except Exception:
            return {"error": "Invalid JSON"}
    else:
        # Would fetch from Blogger
        return {"posts": "not implemented"}

    graph = InternalLinkGraph()
    stats = graph.build_graph(posts)

    return {
        "total_posts": stats.total_posts,
        "total_links": stats.total_links,
        "orphan_pages": stats.orphan_pages,
        "authority_hubs": stats.authority_hubs,
    }