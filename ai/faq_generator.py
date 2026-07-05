"""
FAQ Generator.

ARCHITECTURAL DECISION: Transformer Pattern
----------------------------------------------
The FAQGenerator transforms content into FAQ format.
Uses AI for natural, engaging questions and answers.
"""

import json
from typing import Optional

from config import get_logger
from ai.models import FAQRequest, FAQResponse, FAQItem
from ai.providers.base import BaseProvider, ProviderConfig
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openrouter_provider import OpenRouterProvider

logger = get_logger("ai", "faq_generator")


class FAQGenerator:
    """
    Generates FAQ sections for blog posts.

    Analyzes content and creates relevant, valuable FAQ items.
    """

    def __init__(self, provider: Optional[BaseProvider] = None) -> None:
        """
        Initialize FAQ generator.

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
            max_tokens=1500,
            temperature=0.5,
        )

        if settings.ai_default_provider == "openrouter":
            return OpenRouterProvider(config)
        elif settings.ai_default_provider == "openai":
            from ai.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(config)

        return AnthropicProvider(config)

    def generate(self, request: FAQRequest) -> FAQResponse:
        """
        Generate FAQ from content.

        Args:
            request: FAQ generation request

        Returns:
            FAQResponse with questions and structured HTML
        """
        logger.info("Generating FAQ", num_questions=request.num_questions)

        faqs = self._provider.generate_faq(
            content=request.content,
            title=request.title,
            num_questions=request.num_questions,
        )

        # Convert to FAQItem objects
        faq_items = [
            FAQItem(question=q, answer=a) for q, a in faqs
        ]

        # Generate structured HTML
        html = self._format_as_html(faq_items, request.style)

        return FAQResponse(
            faqs=faq_items,
            structured_html=html,
        )

    def _format_as_html(self, faqs: list[FAQItem], style: str) -> str:
        """Format FAQs as HTML."""
        if not faqs:
            return ""

        if style == "bullets":
            # Schema.org FAQ markup
            parts = ['<script type="application/ld+json">', '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[']
            for faq in faqs:
                parts.append(f'{{"@type":"Question","name":"{faq.question}","acceptedAnswer":{{"@type":"Answer","text":"{faq.answer}"}}}}')
            parts.append(']}</script>')
            return "".join(parts)

        elif style == "list":
            parts = ["<ul class='faq-list'>"]
            for faq in faqs:
                parts.append(f"<li><strong>{faq.question}</strong> {faq.answer}</li>")
            parts.append("</ul>")
            return "".join(parts)

        else:  # structured
            parts = ["<section class='faq'>"]
            for faq in faqs:
                parts.append(f"<h3>{faq.question}</h3>")
                parts.append(f"<p>{faq.answer}</p>")
            parts.append("</section>")
            return "".join(parts)