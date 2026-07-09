"""
Summary Generator.

ARCHITECTURAL DECISION: Extraction Pattern
--------------------------------------------
The SummaryGenerator extracts key information and creates summaries.
Useful for post excerpts and social media sharing.

Provider selection is handled by the centralized create_provider() factory.
"""

from typing import Optional

from config import get_logger
from ai.models import SummaryRequest, SummaryResponse
from ai.providers.base import BaseProvider
from ai.provider_factory import create_provider

logger = get_logger("ai", "summary_generator")


class SummaryGenerator:
    """
    Generates summaries for blog posts.

    Creates concise, compelling summaries for previews and sharing.
    """

    def __init__(self, provider: Optional[BaseProvider] = None) -> None:
        """
        Initialize summary generator.

        Args:
            provider: Optional provider to use (uses default if None)
        """
        self._provider = provider or create_provider()

    def generate(self, request: SummaryRequest) -> SummaryResponse:
        """
        Generate a summary from content.

        Args:
            request: Summary generation request

        Returns:
            SummaryResponse with summary and optional key points
        """
        logger.info("Generating summary", style=request.style)

        summary = self._provider.generate_summary(
            content=request.content,
            style=request.style,
            max_length=request.max_length,
        )

        key_points = []
        if request.include_key_points:
            key_points = self._extract_key_points(request.content)

        return SummaryResponse(
            summary=summary,
            key_points=key_points,
            original_length=len(request.content),
            summary_length=len(summary),
        )

    def _extract_key_points(self, content: str) -> list[str]:
        """Extract key points from content."""
        # Use the provider to extract key points
        from utils.helpers import extract_text_from_html

        text = extract_text_from_html(content)
        prompt = f"""Extract the 5 key points from this content:

{text[:3000]}

Return one key point per line, no numbering.
"""

        try:
            result = self._provider.generate_text(prompt, max_tokens=300)
            points = [line.strip() for line in result.split("\n") if line.strip()]
            return points[:5]
        except Exception as e:
            logger.warning("Failed to extract key points", error=str(e))
            return []

    def generate_excerpt(self, content: str, max_length: int = 160) -> str:
        """
        Generate a short excerpt for meta description.

        Args:
            content: Full content
            max_length: Maximum length

        Returns:
            Short excerpt
        """
        return self.generate(
            SummaryRequest(content=content, style="brief", max_length=max_length)
        ).summary