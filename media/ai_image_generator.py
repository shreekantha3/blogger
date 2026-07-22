"""
AI Image Generator for custom visuals and diagrams.

ARCHITECTURAL DECISION: AI Image Generation Strategy
----------------------------------------------------
Based on Honest Code Review finding that "Media Engine Has No AI Images".

In 2026, you need DALL-E 3 / Midjourney / Flux integration for:
1. Custom diagrams (not stock photos)
2. Data visualizations from your content
3. Branded OG images (not text-on-gradient)
4. Unique feature images per article

This differentiates content from competitors using generic stock.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import base64
import json

import httpx

from config import get_settings, get_logger

logger = get_logger("media", "ai_image")


@dataclass
class ImageGenerationRequest:
    """Request for AI image generation."""

    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "natural"  # natural or vivid
    format: str = "png"


@dataclass
class ImageGenerationResult:
    """Result of AI image generation."""

    url: Optional[str]  # URL for OpenAI response
    b64_data: Optional[str]  # Base64 data if requested
    revised_prompt: Optional[str]
    error: Optional[str] = None


class AIImageGenerator:
    """
    Generate images using AI models (DALL-E, Flux, Midjourney).

    Usage:
        generator = AIImageGenerator()
        result = await generator.generate_feature_image(
            title="KSP Recruitment Guide",
            topic="Police Exam",
        )
    """

    def __init__(self, openai_api_key: Optional[str] = None) -> None:
        """
        Initialize AI image generator.

        Args:
            openai_api_key: OpenAI API key (from settings if not provided)
        """
        self._settings = get_settings()
        self._api_key = openai_api_key or self._settings.openai_api_key
        self._http_client = httpx.AsyncClient()

    async def generate_feature_image(
        self,
        title: str,
        topic: str,
        brand_colors: Optional[Tuple[str, str]] = None,
    ) -> ImageGenerationResult:
        """
        Generate a custom feature image for blog posts.

        Args:
            title: Blog post title
            topic: Article topic
            brand_colors: Optional tuple of (primary, secondary) colors

        Returns:
            ImageGenerationResult with image data
        """
        color_hint = ""
        if brand_colors:
            color_hint = f" with brand colors {brand_colors[0]} and {brand_colors[1]}"

        prompt = (
            f"Professional blog header image for '{title}', "
            f"topic: {topic}, "
            f"clean minimal style{color_hint}, "
            f"1200x630 aspect ratio, "
            f"clear typography, "
            f"suitable for social media sharing"
        )

        return await self._generate_dalle(prompt)

    async def generate_diagram(
        self,
        concept: str,
        data: dict,
    ) -> ImageGenerationResult:
        """
        Generate a technical diagram from content data.

        Args:
            concept: Diagram concept (e.g., "Application Process Flow")
            data: Data to visualize

        Returns:
            ImageGenerationResult with diagram
        """
        prompt = (
            f"Technical diagram: '{concept}', "
            f"data points: {json.dumps(data)[:200]}, "
            f"clean infographic style, "
            f"white background, "
            f"clear labels and arrows, "
            f"professional illustration"
        )

        return await self._generate_dalle(prompt, size="1024x768")

    async def generate_chart(
        self,
        chart_type: str,
        data: dict,
        title: str,
    ) -> ImageGenerationResult:
        """
        Generate a chart or graph visualization.

        Args:
            chart_type: Type of chart (bar, line, pie, funnel)
            data: Data to plot
            title: Chart title

        Returns:
            ImageGenerationResult with chart image
        """
        prompt = (
            f"{chart_type.capitalize()} chart: '{title}', "
            f"data: {json.dumps(data)[:300]}, "
            f"clean data visualization, "
            f"professional styling, "
            f"clear axis labels, "
            f"accessible color palette"
        )

        return await self._generate_dalle(prompt, size="1024x768")

    async def _generate_dalle(
        self,
        prompt: str,
        size: str = "1024x1024",
    ) -> ImageGenerationResult:
        """Generate image using DALL-E API."""
        if not self._api_key:
            return ImageGenerationResult(
                url=None,
                b64_data=None,
                revised_prompt=None,
                error="No OpenAI API key configured",
            )

        try:
            response = await self._http_client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "size": size,
                    "quality": "standard",
                    "n": 1,
                },
            )

            response.raise_for_status()
            data = response.json()

            logger.info("Generated AI image", prompt=prompt[:50])

            return ImageGenerationResult(
                url=data["data"][0].get("url"),
                revised_prompt=data.get("revised_prompt"),
            )

        except httpx.HTTPStatusError as e:
            logger.error("OpenAI API error", error=str(e))
            return ImageGenerationResult(
                url=None,
                b64_data=None,
                revised_prompt=None,
                error=f"API error: {e.response.status_code}",
            )
        except Exception as e:
            logger.error("Image generation failed", error=str(e))
            return ImageGenerationResult(
                url=None,
                b64_data=None,
                revised_prompt=None,
                error=str(e),
            )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._http_client.aclose()