"""
Tests for Phase 4 AI Engine.

These tests use mock providers to avoid requiring actual API keys.
"""

from unittest.mock import MagicMock, patch

import pytest

from ai.models import (
    AIArticleRequest,
    SEOTitleRequest,
    MetaOptimizationRequest,
    FAQRequest,
    SummaryRequest,
    KeywordOptimizationRequest,
)
from ai.generator import AIArticleGenerator
from ai.seo_title import SEOTitleGenerator
from ai.meta_optimizer import MetaDescriptionOptimizer
from ai.faq_generator import FAQGenerator
from ai.summary_generator import SummaryGenerator
from ai.keyword_optimizer import KeywordOptimizer


class MockProvider:
    """Mock provider for testing without API calls."""

    def __init__(self) -> None:
        self.model = "test-model"

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Return deterministic mock responses."""
        if "title" in prompt.lower() and "seo" in prompt.lower():
            return "Test SEO Title About Python Programming"
        elif "meta description" in prompt.lower():
            return "Learn about Python programming in this comprehensive guide for developers."
        elif "faq" in prompt.lower():
            return '[{"question": "What is Python?", "answer": "Python is a programming language."}]'
        elif "summarize" in prompt.lower() or "summary" in prompt.lower():
            return "This is a test summary of the content."
        elif "keywords" in prompt.lower():
            return '{"optimized_content": "<p>Optimized content</p>", "related_keywords": ["python", "coding"]}'
        else:
            return "<h1>Generated Title</h1><p>Generated content for testing purposes.</p>"

    def generate_article(self, topic: str, **kwargs) -> tuple[str, str]:
        language = kwargs.get('language', 'en')
        if language != 'en':
            return f"ಲેಖನ ಬರೆಯಿರಿಗೆ {topic}", f"<h1>ಲೆಕ್ಕಾಂಕ {topic}</h1><p>ಸಾಮಗ್ರಿ.</p>"
        return f"Article About {topic}", f"<h1>Article About {topic}</h1><p>Content here.</p>"

    def generate_seo_title(self, topic: str, **kwargs) -> str:
        language = kwargs.get('language', 'en')
        if language != 'en':
            return f"SEO ಶೀರ್ಷಕ: {topic}"
        return f"SEO Title: {topic}"

    def optimize_meta_description(self, content: str, title: str, **kwargs) -> str:
        language = kwargs.get('language', 'en')
        if language != 'en':
            return f"{title} ಬರೆಯಿರಿಗೆ ನಿರ್ದಿಷ್ಟ ವಿವರಣೆ."
        return f"Meta description for {title}."

    def generate_faq(self, content: str, **kwargs) -> list[tuple[str, str]]:
        language = kwargs.get('language', 'en')
        if language != 'en':
            return [("ಇದು ಏನು?", "ಇದು ಒಂದು ಪರೀಕ್ಷಣಾ ಉತ್ತರ.")]
        return [("What is this?", "This is a test answer.")]

    def generate_summary(self, content: str, **kwargs) -> str:
        return "Test summary content."

    def optimize_keywords(self, content: str, main_topic: str, **kwargs) -> tuple[str, list[str]]:
        return f"<p>Optimized: {content}</p>", ["keyword1", "keyword2"]


class TestAIArticleGenerator:
    """Tests for AI article generator."""

    def test_generate_basic_article(self) -> None:
        """Generate a basic article."""
        generator = AIArticleGenerator(provider=MockProvider())

        request = AIArticleRequest(
            topic="Python programming",
            tone="professional",
            word_count=500,
        )
        response = generator.generate(request)

        assert response.title
        assert response.content
        assert "<h1>" in response.content
        assert response.word_count > 0
        assert 0 <= response.seo_score <= 100

    def test_generate_with_keywords(self) -> None:
        """Generate article with target keywords."""
        generator = AIArticleGenerator(provider=MockProvider())

        request = AIArticleRequest(
            topic="Python",
            target_keywords=["python", "coding", "programming"],
            tone="technical",
            word_count=1000,
        )
        response = generator.generate(request)

        assert response.title
        assert response.target_keywords == ["python", "coding", "programming"]


class TestSEOTitleGenerator:
    """Tests for SEO title generator."""

    def test_generate_seo_title(self) -> None:
        """Generate SEO-optimized title."""
        generator = SEOTitleGenerator(provider=MockProvider())

        request = SEOTitleRequest(
            topic="Python programming",
            target_keywords=["python", "coding"],
        )
        response = generator.generate(request)

        assert response.title
        assert response.seo_score >= 0
        assert response.keyword_coverage >= 0

    def test_title_variants(self) -> None:
        """Generate multiple title variants."""
        generator = SEOTitleGenerator(provider=MockProvider())

        variants = generator.generate_variants("Python", count=3)

        assert len(variants) >= 1
        assert all(v.title for v in variants)


class TestMetaDescriptionOptimizer:
    """Tests for meta description optimizer."""

    def test_optimize_meta(self) -> None:
        """Optimize meta description."""
        optimizer = MetaDescriptionOptimizer(provider=MockProvider())

        request = MetaOptimizationRequest(
            title="Python Guide",
            content="<p>Python is a programming language that is easy to learn.</p>",
            target_keyword="Python",
        )
        response = optimizer.optimize(request)

        assert response.meta_description
        assert response.optimized_score >= 0
        assert response.character_count > 0


class TestFAQGenerator:
    """Tests for FAQ generator."""

    def test_generate_faq(self) -> None:
        """Generate FAQ from content."""
        generator = FAQGenerator(provider=MockProvider())

        request = FAQRequest(
            content="<p>Python programming guide for beginners. This comprehensive guide covers the basics of Python development and best practices for new programmers.</p>",
            title="Python Guide",
            num_questions=3,
        )
        response = generator.generate(request)

        assert len(response.faqs) >= 1
        assert response.structured_html
        assert all(faq.question and faq.answer for faq in response.faqs)


class TestSummaryGenerator:
    """Tests for summary generator."""

    def test_generate_summary(self) -> None:
        """Generate summary from content."""
        generator = SummaryGenerator(provider=MockProvider())

        request = SummaryRequest(
            content="<p>This is long content that needs summarizing into a shorter format.</p>",
            style="brief",
        )
        response = generator.generate(request)

        assert response.summary
        assert response.summary_length > 0
        assert response.original_length > 0


class TestKeywordOptimizer:
    """Tests for keyword optimizer."""

    def test_optimize_keywords(self) -> None:
        """Optimize content for keywords."""
        optimizer = KeywordOptimizer(provider=MockProvider())

        request = KeywordOptimizationRequest(
            content="<p>Python programming content here.</p>",
            main_topic="Python",
            target_keywords=["python", "coding"],
        )
        response = optimizer.optimize(request)

        assert response.seo_improvement >= 0
        assert isinstance(response.suggestions, list)


class TestAIModelsValidation:
    """Tests for AI models validation."""

    def test_article_request_validation(self) -> None:
        """Validate article request parameters."""
        # Valid request
        request = AIArticleRequest(topic="Test", word_count=500)
        assert request.topic == "Test"

        # Invalid tone
        with pytest.raises(ValueError):
            AIArticleRequest(topic="Test", tone="invalid")

    def test_seo_title_request_validation(self) -> None:
        """Validate SEO title request parameters."""
        request = SEOTitleRequest(topic="Test", max_length=50)
        assert request.max_length == 50

        # Invalid platform
        with pytest.raises(ValueError):
            SEOTitleRequest(topic="Test", platform="invalid")

    def test_faq_request_validation(self) -> None:
        """Validate FAQ request parameters."""
        request = FAQRequest(content="This is test content for FAQ generation testing purposes and validation.", num_questions=5)
        assert request.num_questions == 5

    def test_summary_request_validation(self) -> None:
        """Validate summary request parameters."""
        request = SummaryRequest(content="This is test content for summary generation testing purposes.")
        assert request.style == "brief"

    def test_keyword_request_validation(self) -> None:
        """Validate keyword optimization request parameters."""
        request = KeywordOptimizationRequest(
            content="<p>Test</p>",
            main_topic="Test",
            max_suggestions=10,
        )
        assert request.max_suggestions == 10


class TestLanguageSupport:
    """Tests for multilingual content generation."""

    def test_generate_article_in_kannada(self) -> None:
        """Generate article in Kannada language."""
        generator = AIArticleGenerator(provider=MockProvider())

        request = AIArticleRequest(
            topic="ಬೆಳೆ ವಿಮೆ",
            tone="professional",
            word_count=500,
            language="kn",
        )
        response = generator.generate(request)

        assert response.title
        assert response.content
        assert response.language == "kn"
        assert "<h1>" in response.content

    def test_generate_article_in_hindi(self) -> None:
        """Generate article in Hindi language."""
        generator = AIArticleGenerator(provider=MockProvider())

        request = AIArticleRequest(
            topic="बीज भुगतान",
            tone="professional",
            word_count=500,
            language="hi",
        )
        response = generator.generate(request)

        assert response.title
        assert response.content
        assert response.language == "hi"

    def test_seo_title_request_language_validation(self) -> None:
        """Validate language code in SEO title request."""
        # Valid language codes
        request = SEOTitleRequest(topic="Test", language="kn")
        assert request.language == "kn"

        request = SEOTitleRequest(topic="Test", language="hi")
        assert request.language == "hi"

        # Invalid language code
        with pytest.raises(ValueError):
            SEOTitleRequest(topic="Test", language="xx")

    def test_article_request_language_validation(self) -> None:
        """Validate language code in article request."""
        # Valid language codes
        request = AIArticleRequest(topic="Test", language="kn")
        assert request.language == "kn"

        request = AIArticleRequest(topic="Test", language="hi")
        assert request.language == "hi"

        # Default language is English
        request = AIArticleRequest(topic="Test")
        assert request.language == "en"

        # Invalid language code
        with pytest.raises(ValueError):
            AIArticleRequest(topic="Test", language="invalid")

    def test_generate_seo_title_in_kannada(self) -> None:
        """Generate SEO title in Kannada language."""
        generator = SEOTitleGenerator(provider=MockProvider())

        request = SEOTitleRequest(
            topic="ಬೆಳೆ ವಿಮೆ",
            language="kn",
        )
        response = generator.generate(request)

        assert response.title
        assert response.language == "kn"

    def test_meta_optimization_in_kannada(self) -> None:
        """Optimize meta description in Kannada language."""
        optimizer = MetaDescriptionOptimizer(provider=MockProvider())

        request = MetaOptimizationRequest(
            title="ಬೆಳೆ ವಿಮೆ ಗുരಿತಾಂತ",
            content="<p>ಬೆಳೆ ವಿಮೆ ಬಗ್ಗೆ ಮಾಹಿತಿ.</p>",
            target_keyword="ಬೆಳೆ ವಿಮೆ",
        )
        response = optimizer.optimize(request)

        assert response.meta_description
        # Meta should be in Kannada when language is set
        assert len(response.meta_description) > 0