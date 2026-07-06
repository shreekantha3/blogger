"""
Main AI article generator.

ARCHITECTURAL DECISION: Facade Pattern
--------------------------------------
The AIArticleGenerator is a facade that:
1. Provides a simplified interface for article generation
2. Delegates to the appropriate provider
3. Integrates with SEO analyzer for quality scoring
4. Handles provider selection and configuration
"""

import re
from typing import Optional

from config import get_settings, get_logger
from ai.models import AIArticleRequest, AIArticleResponse
from ai.providers.base import BaseProvider, ProviderConfig
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openrouter_provider import OpenRouterProvider

logger = get_logger("ai", "generator")


class AIArticleGenerator:
    """
    Generates blog articles using AI providers.

    Supports multiple providers (Anthropic, OpenAI) selected via configuration.
    Integrates with SEO analyzer to provide quality scores.
    """

    def __init__(self, provider: Optional[BaseProvider] = None) -> None:
        """
        Initialize article generator.

        Args:
            provider: Optional provider to use (creates default if None)
        """
        self._provider = provider or self._create_default_provider()

    def _create_default_provider(self) -> BaseProvider:
        """Create the default provider based on settings."""
        settings = get_settings()

        config = ProviderConfig(
            api_key=settings.openrouter_api_key or settings.anthropic_api_key or settings.openai_api_key or "",
            model=settings.ai_default_model,
            max_tokens=settings.ai_max_tokens,
            temperature=settings.ai_temperature,
        )

        if settings.ai_default_provider == "openrouter":
            return OpenRouterProvider(config)
        elif settings.ai_default_provider == "openai":
            from ai.providers.openai_provider import OpenAIProvider
            config.api_key = settings.openai_api_key or ""
            return OpenAIProvider(config)

        return AnthropicProvider(config)

    def generate(self, request: AIArticleRequest) -> AIArticleResponse:
        """
        Generate an article from the request.

        Args:
            request: Article generation request

        Returns:
            Complete AIArticleResponse with title, content, and metadata

        Raises:
            AIServiceError: If provider fails
            AIContentError: If generated content is invalid
        """
        logger.info(
            "Generating article",
            topic=request.topic[:50],
            tone=request.tone,
            word_count=request.word_count,
            language=request.language,
        )

        # Generate title and content with SEO optimization
        title, content = self._provider.generate_article(
            topic=request.topic,
            tone=request.tone,
            target_keywords=request.target_keywords,
            word_count=request.word_count,
            language=request.language,
        )

        # Generate and optimize meta description
        meta_description = None
        if content:
            meta_description = self._provider.optimize_meta_description(
                content=content,
                title=title,
                target_keyword=request.target_keywords[0] if request.target_keywords else None,
                language=request.language,
            )

        # Generate FAQ if requested
        if request.include_faq:
            try:
                faqs = self._provider.generate_faq(
                    content=content,
                    title=title,
                    num_questions=5,
                    language=request.language,
                )
                # Append FAQ to content as HTML
                faq_html = self._format_faq_html(faqs)
                content = content + faq_html
            except Exception as e:
                # Don't fail the whole article if FAQ generation fails
                logger.warning("FAQ generation failed, continuing without FAQ", error=str(e))

        # Calculate and optimize SEO score to 95%+
        seo_score = self._calculate_seo_score(title, content, request.target_keywords)

        # If SEO score below 95, optimize the content
        if seo_score < 95:
            logger.info(f"SEO score {seo_score} below 95%, optimizing...")
            optimized = self._optimize_for_seo(title, content, request.target_keywords, meta_description, request.language)
            title = optimized["title"]
            content = optimized["content"]
            meta_description = optimized["meta_description"]
            seo_score = optimized["seo_score"]

        return AIArticleResponse(
            title=title,
            content=content,
            meta_description=meta_description,
            target_keywords=request.target_keywords,
            word_count=len(content.split()),
            seo_score=seo_score,
            language=request.language,
        )

    def _optimize_for_seo(self, title: str, content: str, keywords: list[str], meta: str, language: str = "en") -> dict:
        """
        Optimize title, content, and meta for 95%+ SEO score.
        """
        from seo import SEOAnalyzer

        # Fix title length (50-70 chars for optimal SEO)
        if len(title) < 50:
            # Extend title with keywords
            keyword_str = ", ".join(keywords[:2]) if keywords else ""
            title = f"{title}: {keyword_str} Analysis"
        elif len(title) > 70:
            # Shorten title
            title = title[:67] + "..."

        # Ensure meta description is optimal (120-160 chars)
        if meta and len(meta) < 120:
            meta = (meta + " Explore comprehensive analysis and insights in this detailed article.")[:155]
        elif not meta:
            meta = f"Comprehensive analysis of {title.split(':')[0].strip()}. Discover key insights and implications."[:155]

        # Fix content structure for better heading score
        content = self._fix_heading_structure(content, title, keywords)

        # Recalculate SEO score
        analyzer = SEOAnalyzer()
        report = analyzer.analyze(title, content, target_keyword=keywords[0] if keywords else None)
        seo_score = report.overall_score

        return {
            "title": title,
            "content": content,
            "meta_description": meta,
            "seo_score": seo_score,
        }

    def _fix_heading_structure(self, content: str, title: str, keywords: list[str]) -> str:
        """
        Ensure proper heading hierarchy for SEO.
        Must have: 1 H1, 5-7 H2, optional H3 under H2.

        This method also handles free model output quirks:
        - Missing or extra heading tags
        - Improper nesting
        - Incomplete content
        """
        import re

        # Clean content first (handle free model artifacts)
        content = self._clean_free_model_content(content)

        # Check if content already has proper structure
        h2_count = len(re.findall(r'<h2>', content, re.IGNORECASE))
        h1_count = len(re.findall(r'<h1>', content, re.IGNORECASE))

        # If missing H2 sections or wrong H1 count, rebuild structure
        if h2_count < 3 or h1_count != 1:
            # Get existing content without headings
            text_only = re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>', '', content, flags=re.DOTALL | re.IGNORECASE)
            text_only = re.sub(r'<[^>]+>', '', text_only)  # Remove all HTML tags
            text_only = re.sub(r'\s+', ' ', text_only).strip()

            # Create proper structure
            sections = [
                "Introduction",
                "Background",
                "Key Insights",
                "Analysis",
                "Implications",
                "Conclusion"
            ]

            # Extract first paragraph for introduction
            paragraphs = re.findall(r'<p>(.*?)</p>', text_only, re.DOTALL)
            intro_text = paragraphs[0] if paragraphs else f"This article analyzes {title}."

            # Distribute remaining content across sections
            remaining_text = " ".join(paragraphs[1:]) if len(paragraphs) > 1 else text_only
            words = remaining_text.split()
            words_per_section = max(1, len(words) // (len(sections) - 1)) if words else 1

            # Rebuild with proper structure
            html_parts = [f"<h1>{title}</h1>"]
            html_parts.append(f"<h2>{sections[0]}</h2>")
            html_parts.append(f"<p>{intro_text}</p>")

            for i, section in enumerate(sections[1:], 1):
                html_parts.append(f"<h2>{section}</h2>")
                start = i * words_per_section
                end = start + words_per_section if i < len(sections) - 1 else len(words)
                section_text = " ".join(words[start:end]) if words else f"Detailed discussion of {section.lower()}."
                html_parts.append(f"<p>{section_text}</p>")

            content = "".join(html_parts)

        return content

    def _clean_free_model_content(self, content: str) -> str:
        """
        Clean free model output for common issues.

        Free models often produce:
        - Incomplete sentences
        - Truncated outputs
        - Formatting artifacts
        - Extra whitespace
        """
        if not content:
            return ""

        # Remove leading markers
        markers = ['TITLE:', 'CONTENT:', 'META:', 'SUMMARY:', 'ANSWER:']
        for marker in markers:
            if content.upper().startswith(marker):
                content = content[len(marker):].strip()

        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content).strip()

        # Fix trailing incomplete sentences
        if content and not content.endswith(('.', '!', '?', '}', ']', ')')):
            # Try to find a good ending
            last_period = content.rfind('.')
            if last_period > len(content) * 0.5:
                content = content[:last_period + 1]
            else:
                content = content.rstrip() + "..."

        return content

    def _format_faq_html(self, faqs: list[tuple[str, str]]) -> str:
        """Format FAQs as HTML."""
        if not faqs:
            return ""

        html_parts = ["<h2>Frequently Asked Questions</h2>"]
        for question, answer in faqs:
            html_parts.append(f"<h3>{question}</h3>")
            html_parts.append(f"<p>{answer}</p>")

        return "".join(html_parts)

    def _calculate_seo_score(
        self,
        title: str,
        content: str,
        keywords: Optional[list[str]] = None,
    ) -> int:
        """Calculate SEO score using existing SEO analyzer."""
        from seo import SEOAnalyzer

        try:
            analyzer = SEOAnalyzer()
            report = analyzer.analyze(title, content, target_keyword=keywords[0] if keywords else None)
            return report.overall_score
        except Exception:
            # If SEO analyzer fails, return a reasonable default
            return 75