"""
SEO Title Generator.

ARCHITECTURAL DECISION: Focused Module Pattern
----------------------------------------------
Each AI feature has its own module for:
1. Single responsibility (only title generation)
2. Easy testing and mocking
3. Clear API surface
4. Future extensibility (title variations, A/B testing)
"""

from typing import Optional

from config import get_logger
from ai.models import SEOTitleRequest, SEOTitleResponse
from ai.providers.base import BaseProvider, ProviderConfig
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openrouter_provider import OpenRouterProvider

logger = get_logger("ai", "seo_title")


class SEOTitleGenerator:
    """
    Generates SEO-optimized titles using AI.

    Analyzes keywords and generates titles optimized for search visibility.
    """

    def __init__(self, provider: Optional[BaseProvider] = None) -> None:
        """
        Initialize SEO title generator.

        Args:
            provider: Optional provider to use (creates default if None)
        """
        self._provider = provider or self._create_default_provider()

    def _create_default_provider(self) -> BaseProvider:
        """Create the default provider based on settings."""
        from config import get_settings

        settings = get_settings()

        config = ProviderConfig(
            api_key=settings.openrouter_api_key or settings.anthropic_api_key or settings.openai_api_key or "",
            model=settings.ai_default_model,
            max_tokens=200,
            temperature=0.7,
        )

        if settings.ai_default_provider == "openrouter":
            return OpenRouterProvider(config)
        elif settings.ai_default_provider == "openai":
            from ai.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(config)

        return AnthropicProvider(config)

    def generate(self, request: SEOTitleRequest) -> SEOTitleResponse:
        """
        Generate an SEO-optimized title.

        Args:
            request: SEO title generation request

        Returns:
            SEOTitleResponse with title and quality metrics
        """
        logger.info("Generating SEO title", topic=request.topic[:50], language=request.language)

        title = self._provider.generate_seo_title(
            topic=request.topic,
            target_keywords=request.target_keywords,
            max_length=request.max_length,
            language=request.language,
        )

        # Calculate metrics
        seo_score = self._score_title(title, request.target_keywords)
        keyword_coverage = self._calculate_keyword_coverage(
            title, request.target_keywords
        )

        return SEOTitleResponse(
            title=title,
            seo_score=seo_score,
            keyword_coverage=keyword_coverage,
            language=request.language,
        )

    def generate_variants(
        self,
        topic: str,
        target_keywords: Optional[list[str]] = None,
        count: int = 3,
    ) -> list[SEOTitleResponse]:
        """
        Generate multiple title variants.

        Args:
            topic: Topic for titles
            target_keywords: Keywords to include
            count: Number of variants to generate (1-10)

        Returns:
            List of SEOTitleResponse variants
        """
        results = []
        for i in range(min(count, 10)):
            # Add variation prompt
            variant_request = SEOTitleRequest(
                topic=topic,
                target_keywords=target_keywords,
            )
            results.append(self.generate(variant_request))

        return results

    def _score_title(self, title: str, keywords: Optional[list[str]] = None) -> int:
        """Score title for SEO quality."""
        score = 100
        length = len(title)

        # Length scoring
        if length < 30:
            score -= 30
        elif length > 70:
            score -= 20

        # Keyword coverage
        if keywords:
            coverage = self._calculate_keyword_coverage(title, keywords)
            if coverage < 50:
                score -= 25

        return max(0, score)

    def _calculate_keyword_coverage(
        self,
        title: str,
        keywords: Optional[list[str]] = None,
    ) -> int:
        """Calculate percentage of keywords included in title."""
        if not keywords:
            return 100

        title_lower = title.lower()
        covered = sum(1 for kw in keywords if kw.lower() in title_lower)

        return int((covered / len(keywords)) * 100) if keywords else 100