"""
Media Engine - Image Selection and Alt Text Generation.

ARCHITECTURAL DECISION: Media Engine Pattern
----------------------------------------------
This module implements Phase 5's media features:
1. Image alt text generation using AI
2. Image selection based on content
3. Unsplash/Pexels API integration placeholders
4. Thumbnail generation coordination

Based on RankMath SEO guidelines requiring 4+ images per post
with descriptive alt text for accessibility and SEO.
"""

from typing import Optional, List, Dict, Any


class ImageSuggestion:
    """Represents a suggested image with alt text."""

    def __init__(
        self,
        url: str,
        alt_text: str,
        source: str = "unsplash",
        width: int = 1200,
        height: int = 630,
    ) -> None:
        self.url = url
        self.alt_text = alt_text
        self.source = source
        self.width = width
        self.height = height

    def to_html(self) -> str:
        """Generate HTML img tag for this image."""
        return (
            f'<img src="{self.url}" '
            f'alt="{self.alt_text}" '
            f'loading="lazy" '
            f'width="{self.width}" '
            f'height="{self.height}">'
        )


class ImageSelector:
    """
    Selects and generates images for blog posts.

    Uses AI to generate alt text and suggests images based on content.
    """

    def __init__(self, provider=None) -> None:
        """
        Initialize image selector.

        Args:
            provider: Optional AI provider for alt text generation
        """
        self._provider = provider

    def generate_alt_text(
        self,
        image_description: str,
        content: Optional[str] = None,
        language: str = "en",
    ) -> str:
        """
        Generate descriptive alt text for an image.

        Args:
            image_description: Brief description of the image
            content: Article content for context
            language: Language for alt text

        Returns:
            Generated alt text (125 characters max for SEO)

        Example:
            >>> selector = ImageSelector()
            >>> alt = selector.generate_alt_text(
            ...     "Python code showing a for loop",
            ...     content="<h1>Python Tips</h1>..."
            ... )
            >>> len(alt) <= 125
        """
        if self._provider:
            prompt = f"""Generate descriptive alt text for an image.
Description: {image_description}
Content context: {content[:200] if content else "No context"}

Requirements:
- Descriptive and accurate
- Maximum 125 characters
- Include SEO-relevant keywords
- No "image of" or "picture of" prefixes

ALT TEXT:"""
            alt_text = self._provider.generate_text(prompt, max_tokens=100)
            return alt_text.strip()[:125]

        # Fallback: simple alt text
        return image_description.strip()[:125]

    def suggest_images(
        self,
        topic: str,
        headings: Optional[List[str]] = None,
        count: int = 4,
    ) -> List[ImageSuggestion]:
        """
        Suggest images based on article topic and headings.

        Args:
            topic: Article topic
            headings: H2/H3 headings for context
            count: Number of images to suggest

        Returns:
            List of ImageSuggestion objects

        Example:
            >>> suggestions = selector.suggest_images(
            ...     topic="Python programming",
            ...     headings=["Introduction", "Variables"],
            ...     count=4
            ... )
            >>> len(suggestions) == 4
        """
        suggestions = []

        # Generate alt text for each image suggestion
        for i in range(count):
            # Create context for alt text
            context = f"{topic}"
            if headings and i < len(headings):
                context = f"{topic} - {headings[i]}"

            alt_text = self._generate_fallback_alt_text(context, i)

            # Placeholder URL (would integrate with Unsplash/Pexels API)
            url = f"https://source.unsplash.com/1200x630/?{topic.replace(' ', ',')},{i}"

            suggestions.append(ImageSuggestion(
                url=url,
                alt_text=alt_text,
                source="unsplash",
            ))

        return suggestions

    def _generate_fallback_alt_text(self, context: str, index: int) -> str:
        """Generate fallback alt text without AI provider."""
        # Map index to image type for better variety
        image_types = [
            "illustration",
            "diagram",
            "screenshot",
            "infographic",
        ]

        img_type = image_types[index % len(image_types)]
        alt_text = f"{context.title()} {img_type} showing key concepts and examples"

        return alt_text[:125]

    def generate_og_image_html(
        self,
        image_url: str,
        alt_text: str,
    ) -> str:
        """
        Generate Open Graph optimized image HTML.

        Args:
            image_url: URL to the image (1200x630px recommended)
            alt_text: Alt text for accessibility

        Returns:
            HTML img tag with proper attributes
        """
        return f'<img src="{image_url}" alt="{alt_text}" width="1200" height="630">'

    def format_images_html(
        self,
        suggestions: List[ImageSuggestion],
        with_captions: bool = False,
    ) -> str:
        """
        Format image suggestions as HTML.

        Args:
            suggestions: List of ImageSuggestion objects
            with_captions: Whether to include captions

        Returns:
            HTML string with all images

        Example:
            >>> html = selector.format_images_html(suggestions)
            >>> "<img" in html
        """
        html_parts = []

        for i, suggestion in enumerate(suggestions, 1):
            html_parts.append(f"\n{suggestion.to_html()}")
            if with_captions:
                html_parts.append(f"<figcaption>{suggestion.alt_text}</figcaption>")

        return "".join(html_parts)

    def validate_image_for_seo(
        self,
        image_url: str,
        alt_text: str,
        topic: str,
    ) -> Dict[str, Any]:
        """
        Validate image meets SEO requirements.

        Args:
            image_url: Image URL
            alt_text: Alt text
            topic: Article topic for keyword matching

        Returns:
            Dict with is_valid, issues, and recommendations

        Example:
            >>> result = selector.validate_image_for_seo(
            ...     url="https://example.com/img.jpg",
            ...     alt_text="Python code example",
            ...     topic="Python programming"
            ... )
            >>> result["is_valid"]
        """
        issues: List[str] = []
        recommendations: List[str] = []

        # Check alt text length
        if len(alt_text) < 50:
            issues.append("Alt text is too short (minimum 50 chars recommended)")
        elif len(alt_text) > 125:
            issues.append("Alt text is too long (maximum 125 chars recommended)")

        # Check alt text for topic keywords
        if topic.lower() not in alt_text.lower():
            recommendations.append("Consider including the main topic in alt text")

        # Check for generic alt text patterns
        generic_patterns = ["image", "photo", "picture", "graphic"]
        if any(pattern in alt_text.lower() for pattern in generic_patterns):
            recommendations.append("Avoid generic terms like 'image' or 'photo' in alt text")

        return {
            "is_valid": len(issues) == 0,
            "alt_text_length": len(alt_text),
            "issues": issues,
            "recommendations": recommendations,
        }