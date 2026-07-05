"""
Keyword Optimizer.

ARCHITECTURAL DECISION: Enhancement Pattern
-----------------------------------------------
The KeywordOptimizer enhances the SEO keyword analyzer by using AI
to suggest related keywords and optimize content density.
"""

from typing import Optional

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