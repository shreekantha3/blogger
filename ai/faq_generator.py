"""
FAQ Generator.

ARCHITECTURAL DECISION: Transformer Pattern
----------------------------------------------
The FAQGenerator transforms content into FAQ format.
Uses AI for natural, engaging questions and answers.

Provider selection is handled by the centralized create_provider() factory.
"""

import json
from typing import Optional

from config import get_logger
from ai.models import FAQRequest, FAQResponse, FAQItem
from ai.providers.base import BaseProvider
from ai.provider_factory import create_provider

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
            provider: Optional provider to use (uses default if None)
        """
        self._provider = provider or create_provider()

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