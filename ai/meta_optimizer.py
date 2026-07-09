"""
Meta Description Optimizer.

ARCHITECTURAL DECISION: Enhancement Pattern
----------------------------------------------
The MetaDescriptionOptimizer enhances existing SEO meta functionality
by using AI for better, more engaging meta descriptions.

Provider selection is handled by the centralized create_provider() factory.
Uses free OpenRouter models by default for cost-effective testing.
"""

from typing import Optional, List, Dict, Any

from config import get_logger
from ai.models import MetaOptimizationRequest, MetaOptimizationResponse
from ai.providers.base import BaseProvider
from ai.provider_factory import create_provider

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
            provider: Optional provider to use (uses default if None)
        """
        self._provider = provider or create_provider()

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

    def generate_open_graph_tags(
        self,
        title: str,
        description: str,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate Open Graph meta tags for social media sharing.

        Args:
            title: Article title (50-60 chars recommended)
            description: Meta description (120-160 chars)
            url: Article URL
            image_url: Featured image URL (1200x630px recommended)

        Returns:
            Dict of OG tag names to values

        Example:
            >>> tags = optimizer.generate_open_graph_tags(
            ...     title="Python Tips",
            ...     description="Learn Python with these tips",
            ...     url="https://example.com/python-tips",
            ...     image_url="https://example.com/og-image.jpg"
            ... )
        """
        og_tags = {
            "og:title": title[:60],
            "og:description": description[:160],
            "og:type": "article",
            "og:site_name": "Blogger Automation Platform",
        }

        if url:
            og_tags["og:url"] = url

        if image_url:
            og_tags["og:image"] = image_url
            og_tags["og:image:width"] = "1200"
            og_tags["og:image:height"] = "630"

        return og_tags

    def generate_twitter_card_tags(
        self,
        title: str,
        description: str,
        image_url: Optional[str] = None,
        creator: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate Twitter Card meta tags.

        Args:
            title: Article title
            description: Meta description
            image_url: Image URL (1200x630px recommended)
            creator: Twitter handle of creator

        Returns:
            Dict of Twitter tag names to values

        Example:
            >>> tags = optimizer.generate_twitter_card_tags(
            ...     title="Python Tips",
            ...     description="Learn Python with these tips",
            ...     image_url="https://example.com/twitter-image.jpg"
            ... )
        """
        twitter_tags = {
            "twitter:card": "summary_large_image",
            "twitter:title": title[:60],
            "twitter:description": description[:160],
        }

        if image_url:
            twitter_tags["twitter:image"] = image_url

        if creator:
            # Ensure @ prefix
            if not creator.startswith("@"):
                creator = "@" + creator
            twitter_tags["twitter:creator"] = creator

        return twitter_tags

    def generate_social_meta_tags(
        self,
        title: str,
        description: str,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
        creator: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate all social media meta tags (OG + Twitter).

        This is a convenience method that combines Open Graph and Twitter Card tags.

        Args:
            title: Article title
            description: Meta description
            url: Article URL
            image_url: Featured image URL
            creator: Twitter handle

        Returns:
            Combined dict of all social meta tags
        """
        og_tags = self.generate_open_graph_tags(
            title=title,
            description=description,
            url=url,
            image_url=image_url,
        )

        twitter_tags = self.generate_twitter_card_tags(
            title=title,
            description=description,
            image_url=image_url,
            creator=creator,
        )

        return {**og_tags, **twitter_tags}

    def format_social_tags_html(self, tags: Dict[str, str]) -> str:
        """
        Format social meta tags as HTML meta tags.

        Args:
            tags: Dict of tag names to values

        Returns:
            HTML string with meta tags
        """
        html_parts = []
        for name, content in tags.items():
            if name.startswith("twitter:"):
                html_parts.append(f'<meta name="{name}" content="{content}">')
            else:
                html_parts.append(f'<meta property="{name}" content="{content}">')

        return "\n".join(html_parts)
