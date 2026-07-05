"""
Meta Description Optimizer.

ARCHITECTURAL DECISION: Enhancement Pattern
----------------------------------------------
The MetaDescriptionOptimizer enhances existing SEO meta functionality
by using AI for better, more engaging meta descriptions.
"""

from typing import Optional

from config import get_logger
from ai.models import MetaOptimizationRequest, MetaOptimizationResponse
from ai.providers.base import BaseProvider, ProviderConfig
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openrouter_provider import OpenRouterProvider

logger = get_logger("ai", "meta_optimizer")


class MetaDescriptionOptimizer:
    """
    Optimizes meta descriptions using AI.

    Improves upon the SEO meta generator by creating
    more compelling, conversion-focused descriptions.
    """

    def __init__(self, provider: Optional[BaseProvider] = None) -> None:
        """
        Initialize meta optimizer.

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
            max_tokens=200,
            temperature=0.5,
        )

        if settings.ai_default_provider == "openrouter":
            return OpenRouterProvider(config)
        elif settings.ai_default_provider == "openai":
            from ai.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(config)

        return AnthropicProvider(config)

    def optimize(self, request: MetaOptimizationRequest) -> MetaOptimizationResponse:
        """
        Generate or optimize a meta description.

        Args:
            request: Meta optimization request

        Returns:
            MetaOptimizationResponse with optimized meta and metrics
        """
        logger.info("Optimizing meta description", title=request.title[:50])

        # Generate optimized meta
        optimized = self._provider.optimize_meta_description(
            content=request.content,
            title=request.title,
            target_keyword=request.target_keyword,
            length=request.length,
        )

        # Fallback: Validate the AI output - if it looks like instructions, use rule-based
        optimized = self._sanitize_meta_description(optimized, request.title)

        # Score original (basic heuristic)
        original_score = self._basic_meta_score(request.content[:155])

        # Score optimized meta
        from seo.meta import MetaDescriptionGenerator
        validator = MetaDescriptionGenerator()
        optimized_score = validator.validate(optimized).value

        return MetaOptimizationResponse(
            meta_description=optimized,
            original_score=original_score,
            optimized_score=optimized_score,
            character_count=len(optimized),
        )

    def _sanitize_meta_description(self, meta: str, title: str) -> str:
        """
        Sanitize meta description - fall back to rule-based if AI output is corrupted.

        Design decision: Defensive programming - free models often return prompt echo.
        This ensures we always have a valid meta description.
        """
        # Check if meta looks like it contains instructions (corrupted output)
        corruption_indicators = [
            "meta description",
            "we need",
            "write a meta",
            "characters",
            "requirements:",
            "format:",
        ]

        meta_lower = meta.lower()
        if any(indicator in meta_lower for indicator in corruption_indicators):
            # Fallback to rule-based generation
            from seo.meta import MetaDescriptionGenerator
            generator = MetaDescriptionGenerator()
            logger.warning("AI meta description corrupted, falling back to rule-based generation")
            return generator.generate(f"<h1>{title}</h1><p>{meta}</p>", title=title)[:155]

        return meta[:155]

    def _basic_meta_score(self, text: str) -> int:
        """Calculate basic score for text."""
        if not text:
            return 0
        length = len(text)
        if length < 80:
            return 40
        elif length < 120:
            return 70
        elif length <= 160:
            return 90
        return 75