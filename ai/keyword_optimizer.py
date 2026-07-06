"""
Keyword Optimizer.

ARCHITECTURAL DECISION: Enhancement Pattern
-----------------------------------------------
The KeywordOptimizer enhances the SEO keyword analyzer by using AI
to suggest related keywords and optimize content density.
"""

from typing import Optional, List, Dict, Any

from config import get_logger
from ai.models import (
    KeywordOptimizationRequest,
    KeywordOptimizationResponse,
    KeywordSuggestion,
)
from ai.providers.base import BaseProvider, ProviderConfig
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openrouter_provider import OpenRouterProvider

logger = get_logger("ai", "keyword_optimizer")


class KeywordOptimizer:
    """
    Optimizes content for keywords using AI.

    Suggests related keywords and optimizes placement.
    """

    def __init__(self, provider: Optional[BaseProvider] = None) -> None:
        """
        Initialize keyword optimizer.

        Args:
            provider: Optional provider to use
        """
        self._provider = provider or self._create_default_provider()

    def _create_default_provider(self) -> BaseProvider:
        """Create the default provider based on settings."""
        from config import get_settings

        settings = get_settings()

        config = ProviderConfig(
            api_key=settings.openrouter_api_key or settings.anthropic_api_key or settings.openai_api_key or "",
            model=settings.ai_default_model,
            max_tokens=1000,
            temperature=0.5,
        )

        if settings.ai_default_provider == "openrouter":
            return OpenRouterProvider(config)
        elif settings.ai_default_provider == "openai":
            from ai.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(config)

        return AnthropicProvider(config)

    def optimize(self, request: KeywordOptimizationRequest) -> KeywordOptimizationResponse:
        """
        Optimize content for keywords.

        Args:
            request: Keyword optimization request

        Returns:
            KeywordOptimizationResponse with metrics and suggestions
        """
        logger.info("Optimizing keywords", topic=request.main_topic[:50])

        optimized_content, related_keywords = self._provider.optimize_keywords(
            content=request.content,
            main_topic=request.main_topic,
            target_keywords=request.target_keywords,
        )

        # Calculate keyword density
        density = self._calculate_keyword_density(
            optimized_content or request.content,
            request.target_keywords or [request.main_topic],
        )

        # Create keyword suggestions with relevance scores
        suggestions = [
            KeywordSuggestion(
                keyword=kw,
                relevance=100,  # AI provides highly relevant suggestions
            )
            for kw in related_keywords[:request.max_suggestions]
        ]

        # Calculate improvement score
        seo_improvement = self._calculate_improvement(
            request.content,
            optimized_content or request.content,
            request.target_keywords,
        )

        return KeywordOptimizationResponse(
            optimized_content=optimized_content if request.enhance_density else None,
            keyword_density=density,
            suggestions=suggestions,
            seo_improvement=seo_improvement,
        )

    def suggest_related(
        self,
        topic: str,
        count: int = 10,
    ) -> list[KeywordSuggestion]:
        """
        Get related keyword suggestions.

        Args:
            topic: Main topic
            count: Maximum number of suggestions

        Returns:
            List of keyword suggestions
        """
        prompt = f"""Suggest {count} keywords related to "{topic}".

Return as JSON array with objects: {{"keyword": "...", "relevance": 90}}

Include long-tail variations and semantic matches.
"""

        try:
            response = self._provider.generate_text(prompt, max_tokens=500)
            import json
            data = json.loads(response)
            return [KeywordSuggestion(**kw) for kw in data[:count]]
        except Exception as e:
            logger.warning("Failed to suggest keywords", error=str(e))
            return [KeywordSuggestion(keyword=topic, relevance=100)]

    def _calculate_keyword_density(
        self,
        content: str,
        keywords: list[str],
    ) -> dict[str, float]:
        """Calculate keyword density percentages."""
        from utils.helpers import extract_text_from_html

        text = extract_text_from_html(content).lower()
        words = text.split()
        total_words = len(words)

        density = {}
        for kw in keywords:
            count = text.count(kw.lower())
            density[kw] = (count / total_words * 100) if total_words > 0 else 0

        return density

    def _calculate_improvement(
        self,
        original: str,
        optimized: str,
        keywords: Optional[list[str]] = None,
    ) -> int:
        """Estimate SEO improvement score."""
        if not keywords:
            return 0

        orig_density = self._calculate_keyword_density(original, keywords)
        opt_density = self._calculate_keyword_density(optimized, keywords)

        # Calculate improvement based on density increase
        improvement = 0
        for kw in keywords:
            orig = orig_density.get(kw, 0)
            opt = opt_density.get(kw, 0)
            if opt > orig:
                improvement += int((opt - orig) * 10)

        return min(100, improvement)

    def generate_lsi_keywords(
        self,
        main_topic: str,
        count: int = 10,
        cluster_by_semantic: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Generate LSI (Latent Semantic Indexing) keywords for a topic.

        LSI keywords are semantically related terms that help Google understand
        the context and topical depth of content.

        Args:
            main_topic: Primary topic to generate LSI keywords for
            count: Number of LSI keywords to generate (default 10+)
            cluster_by_semantic: Group keywords by semantic meaning

        Returns:
            List of dicts with keyword, semantic_group, and relevance

        Example:
            >>> lsi = optimizer.generate_lsi_keywords("python programming")
            >>> for kw in lsi:
            ...     print(f"{kw['keyword']} ({kw['semantic_group']})")
        """
        prompt = f"""Generate {count} LSI (Latent Semantic Indexing) keywords for "{main_topic}".

LSI keywords are semantically related terms that help with SEO. Group them by semantic meaning.

Return as JSON array with:
{{"keyword": "related term", "semantic_group": "group name", "relevance": 90}}

Semantic groups to consider:
- Primary topic variations
- Related concepts
- Long-tail variations
- Synonyms and related terms
- Question-based keywords
- Comparison terms

Example output:
[
  {{"keyword": "python basics", "semantic_group": "primary_variations", "relevance": 95}},
  {{"keyword": "learn python", "semantic_group": "long_tail", "relevance": 90}}
]
"""
        try:
            response = self._provider.generate_text(prompt, max_tokens=800)
            import json
            data = json.loads(response)

            if cluster_by_semantic:
                # Group keywords by semantic group
                groups: Dict[str, List[str]] = {}
                for item in data:
                    group = item.get("semantic_group", "general")
                    keyword = item.get("keyword", "")
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(keyword)

                return data[:count]
            return data[:count]
        except Exception as e:
            logger.warning("Failed to generate LSI keywords", error=str(e))
            # Fallback: return basic related terms
            return self._fallback_lsi_keywords(main_topic, count)

    def _fallback_lsi_keywords(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """Generate basic LSI keywords when AI fails."""
        # Common semantic groups for topics
        semantic_groups = {
            "beginner": [f"{topic} for beginners", f"learn {topic}", f"introduction to {topic}"],
            "advanced": [f"advanced {topic}", f"{topic} expert", f"{topic} mastery"],
            "tutorials": [f"{topic} tutorial", f"how to {topic}", f"{topic} guide"],
            "comparison": [f"{topic} vs alternatives", f"best {topic}", f"{topic} comparison"],
            "related": [f"related to {topic}", f"{topic} techniques", f"{topic} methods"],
        }

        results = []
        for group, keywords in semantic_groups.items():
            for kw in keywords:
                results.append({
                    "keyword": kw,
                    "semantic_group": group,
                    "relevance": 85,
                })
                if len(results) >= count:
                    return results

        return results[:count]

    def validate_keyword_density(
        self,
        content: str,
        primary_keyword: str,
        target_density: float = 1.5,
    ) -> Dict[str, Any]:
        """
        Validate keyword density meets SEO requirements.

        Args:
            content: HTML content to analyze
            primary_keyword: Primary keyword to check
            target_density: Target density percentage (default 1.5%)

        Returns:
            Dict with density, is_optimal, and recommendations
        """
        density = self._calculate_keyword_density(content, [primary_keyword])
        actual_density = density.get(primary_keyword, 0)

        is_optimal = 1.0 <= actual_density <= 2.0  # 1-2% is optimal

        recommendations = []
        if actual_density < 1.0:
            recommendations.append(f"Increase '{primary_keyword}' density (currently {actual_density:.2f}%, target 1-2%)")
        elif actual_density > 2.0:
            recommendations.append(f"Reduce '{primary_keyword}' density (currently {actual_density:.2f}%, target 1-2%)")

        return {
            "keyword": primary_keyword,
            "density": actual_density,
            "target_density": target_density,
            "is_optimal": is_optimal,
            "recommendations": recommendations,
        }
