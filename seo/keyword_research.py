"""
Keyword research module for finding content opportunities.

ARCHITECTURAL DECISION: Keyword Research Strategy
-------------------------------------------------
Based on Honest Code Review finding that "You have KeywordAnalyzer (checks density)
but not KeywordResearcher (finds opportunities)."

This module:
1. Finds keywords with search volume and difficulty
2. Clusters by search intent (informational, commercial, transactional)
3. Identifies "easy wins" (low difficulty, decent volume)
4. Maps to content pillars

Addresses "What to write" - the missing strategic layer.
"""

from dataclasses import dataclass
from typing import Optional
import re

from config import get_settings, get_logger

logger = get_logger("seo", "keywords")


@dataclass
class KeywordOpportunity:
    """A keyword opportunity with metrics."""

    keyword: str
    search_volume: int
    difficulty: float  # 0-100 scale
    cpc: Optional[float] = None
    intent: str = "informational"  # informational, commercial, transactional
    competition: str = "medium"  # low, medium, high
    serp_features: list[str] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.serp_features is None:
            self.serp_features = []


@dataclass
class KeywordCluster:
    """Group of related keywords."""

    main_keyword: str
    related_keywords: list[str]
    total_volume: int
    average_difficulty: float
    intent: str
    pillar_topic: Optional[str] = None


class KeywordResearcher:
    """
    Research and analyze keyword opportunities.

    Usage:
        researcher = KeywordResearcher()
        opportunities = researcher.find_opportunities("python")
        easy_wins = [k for k in opportunities if k.difficulty < 30]
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize keyword researcher.

        Args:
            api_key: API key for keyword research service (optional)
        """
        self._settings = get_settings()
        self._api_key = api_key

    def find_opportunities(
        self,
        seed_keyword: str,
        limit: int = 50,
    ) -> list[KeywordOpportunity]:
        """
        Find keyword opportunities related to seed keyword.

        Args:
            seed_keyword: Starting keyword
            limit: Maximum keywords to return

        Returns:
            List of KeywordOpportunity objects
        """
        # For now, generate synthetic opportunities
        # In production, integrate with:
        # - GSC API (free, your own data)
        # - Google Trends API
        # - Ubersuggest API
        # - Free SERP scrapers

        opportunities = self._generate_suggestions(seed_keyword, limit)

        # Sort by opportunity score
        opportunities.sort(key=lambda k: self._opportunity_score(k), reverse=True)

        logger.info(
            "Found keyword opportunities",
            seed=seed_keyword,
            count=len(opportunities),
        )

        return opportunities

    def _generate_suggestions(
        self,
        seed: str,
        limit: int,
    ) -> list[KeywordOpportunity]:
        """Generate keyword suggestions (mock implementation)."""

        # Based on keyword type, suggest variations
        modifiers = [
            "how to", "guide", "tutorial", "tips",
            "best", "top", "2025", "2026",
            "complete", "ultimate", "beginner",
        ]

        opportunities = []

        # Add seed keyword
        opportunities.append(KeywordOpportunity(
            keyword=seed,
            search_volume=1000 + hash(seed) % 5000,
            difficulty=30 + hash(seed) % 50,
        ))

        # Add modified variations
        for modifier in modifiers[:limit - 1]:
            keyword = f"{modifier} {seed}"
            opportunities.append(KeywordOpportunity(
                keyword=keyword,
                search_volume=500 + hash(keyword) % 2000,
                difficulty=20 + hash(keyword) % 40,
            ))

        return opportunities

    def _opportunity_score(self, kw: KeywordOpportunity) -> float:
        """Calculate opportunity score (higher = better)."""
        # Simple formula: volume / difficulty
        if kw.difficulty == 0:
            return kw.search_volume
        return kw.search_volume / (kw.difficulty / 10)

    def cluster_keywords(
        self,
        keywords: list[str],
    ) -> list[KeywordCluster]:
        """
        Cluster keywords by intent and topic.

        Args:
            keywords: List of keywords to cluster

        Returns:
            List of KeywordCluster objects
        """
        clusters = []

        for kw in keywords:
            intent = self._determine_intent(kw)
            cluster = KeywordCluster(
                main_keyword=kw,
                related_keywords=[k for k in keywords if k != kw][:5],
                total_volume=self._estimate_volume(kw),
                average_difficulty=self._estimate_difficulty(kw),
                intent=intent,
                pillar_topic=kw.split()[0] if kw else "",
            )
            clusters.append(cluster)

        return clusters

    def _determine_intent(self, keyword: str) -> str:
        """Determine search intent from keyword."""
        keyword_lower = keyword.lower()

        if any(w in keyword_lower for w in ["how", "what", "guide", "tutorial"]):
            return "informational"
        if any(w in keyword_lower for w in ["buy", "price", "cost", "order"]):
            return "transactional"
        if any(w in keyword_lower for w in ["best", "review", "compare", "vs"]):
            return "commercial"

        return "informational"

    def _estimate_volume(self, keyword: str) -> int:
        """Estimate search volume for keyword."""
        # Mock - in production use API
        return 1000 + len(keyword) * 100 + hash(keyword) % 1000

    def _estimate_difficulty(self, keyword: str) -> float:
        """Estimate keyword difficulty."""
        # Mock - in production use API
        # Shorter, more generic keywords = higher difficulty
        word_count = len(keyword.split())
        base = 50 if word_count == 1 else 30
        return max(10, base - word_count * 5)


def find_easy_wins(
    opportunities: list[KeywordOpportunity],
    max_difficulty: float = 30.0,
    min_volume: int = 100,
) -> list[KeywordOpportunity]:
    """
    Filter for easy win keywords.

    Args:
        opportunities: All keyword opportunities
        max_difficulty: Maximum difficulty score (lower = easier)
        min_volume: Minimum search volume

    Returns:
        Filtered list of easy wins
    """
    return [
        k for k in opportunities
        if k.difficulty <= max_difficulty and k.search_volume >= min_volume
    ]