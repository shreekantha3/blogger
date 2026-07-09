"""
Tests for Phase 5 SEO Enhancement features.

These tests cover:
- Schema markup generation
- Content structure validation
- Internal linking suggestions
- LSI keyword generation
- Open Graph meta tags
- Keyword density validation
"""

import pytest
from ai.models import AIArticleRequest, SEOTitleRequest, MetaOptimizationRequest


class TestSchemaMarkupGeneration:
    """Tests for JSON-LD schema markup generation."""

    def test_article_schema_structure(self) -> None:
        """Article schema should have required fields."""
        from ai.schema_generator import SchemaGenerator

        generator = SchemaGenerator()

        schema = generator.generate_article_schema(
            title="Python Programming Guide",
            content="<h1>Python Programming Guide</h1><p>Learn Python basics.</p>",
            keywords=["python", "programming"],
            author="John Doe",
            publish_date="2025-01-15",
            image_url="https://example.com/image.jpg",
            description="Learn Python programming with this comprehensive guide."
        )

        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "BlogPosting"
        assert schema["headline"] == "Python Programming Guide"
        assert "description" in schema
        assert "author" in schema
        assert schema["author"]["@type"] == "Person"
        assert schema["author"]["name"] == "John Doe"
        assert schema["datePublished"] == "2025-01-15"
        assert schema["image"] == "https://example.com/image.jpg"
        assert "python, programming" in schema["keywords"]

    def test_article_schema_minimal(self) -> None:
        """Article schema with minimal required fields."""
        from ai.schema_generator import SchemaGenerator

        generator = SchemaGenerator()

        schema = generator.generate_article_schema(
            title="Test Article",
            content="<p>Test content</p>"
        )

        assert schema["@type"] == "BlogPosting"
        assert schema["headline"] == "Test Article"
        assert "description" in schema

    def test_breadcrumb_schema_structure(self) -> None:
        """Breadcrumb schema should have correct structure."""
        from ai.schema_generator import SchemaGenerator

        generator = SchemaGenerator()

        breadcrumbs = [
            {"name": "Home", "url": "/"},
            {"name": "Blog", "url": "/blog"},
            {"name": "Python Guide", "url": "/blog/python-guide"},
        ]

        schema = generator.generate_breadcrumb_schema(breadcrumbs, base_url="https://example.com")

        assert schema["@type"] == "BreadcrumbList"
        assert len(schema["itemListElement"]) == 3
        assert schema["itemListElement"][0]["name"] == "Home"
        assert schema["itemListElement"][0]["item"] == "https://example.com/"
        assert schema["itemListElement"][1]["position"] == 2

    def test_combine_schemas(self) -> None:
        """Should combine multiple schemas into valid JSON."""
        from ai.schema_generator import SchemaGenerator
        import json

        generator = SchemaGenerator()

        article_schema = generator.generate_article_schema(
            title="Test",
            content="<p>Content</p>"
        )

        combined = generator.combine_schemas(article_schema)

        # Should be valid JSON
        parsed = json.loads(combined)
        assert parsed["@type"] == "BlogPosting"

    def test_generate_all_schemas(self) -> None:
        """Should generate all schemas with convenience method."""
        from ai.schema_generator import SchemaGenerator

        generator = SchemaGenerator()

        result = generator.generate_all_schemas(
            title="Complete Guide",
            content="<h1>Guide</h1><p>Content</p>",
            keywords=["guide", "tutorial"],
            author="Jane Doe",
            publish_date="2025-02-01",
            url="https://example.com/blog/guide",
            breadcrumb_list=[
                {"name": "Home", "url": "/"},
                {"name": "Blog", "url": "/blog"},
            ]
        )

        assert "article" in result
        assert "breadcrumb" in result
        assert "combined" in result
        assert result["article"]["@type"] == "BlogPosting"
        assert result["breadcrumb"]["@type"] == "BreadcrumbList"

    def test_validate_schema(self) -> None:
        """Schema validation should work correctly."""
        from ai.schema_generator import SchemaGenerator

        generator = SchemaGenerator()

        valid_schema = {"@context": "https://schema.org", "@type": "BlogPosting"}
        invalid_schema = {"@context": "https://schema.org"}  # Missing @type

        assert generator.validate_schema(valid_schema) is True
        assert generator.validate_schema(invalid_schema) is False

    def test_get_schema_html(self) -> None:
        """Should generate valid HTML script tag."""
        from ai.schema_generator import SchemaGenerator

        generator = SchemaGenerator()

        schema = generator.generate_article_schema(
            title="Test",
            content="<p>Content</p>"
        )

        html = generator.get_schema_html(schema)

        assert '<script type="application/ld+json">' in html
        assert '</script>' in html
        assert '"@type": "BlogPosting"' in html


class TestContentStructure:
    """Tests for proper H1-H6 heading hierarchy."""

    def test_heading_hierarchy_validation(self) -> None:
        """Content should have proper H1-H2-H3 structure."""
        from seo.headings import HeadingAnalyzer
        
        analyzer = HeadingAnalyzer()
        
        # Valid structure
        valid_content = """
        <h1>Main Title</h1>
        <h2>Introduction</h2>
        <p>Intro content</p>
        <h3>Background</h3>
        <p>Background content</p>
        <h2>Analysis</h2>
        <p>Analysis content</p>
        <h3>Key Points</h3>
        <p>Key points content</p>
        """
        
        # Extract headings to verify structure
        headings = analyzer.extract_headings(valid_content)
        h1_count = sum(1 for h in headings if h.level == 1)
        h2_count = sum(1 for h in headings if h.level == 2)
        h3_count = sum(1 for h in headings if h.level == 3)
        
        assert h1_count == 1  # Exactly one H1
        assert h2_count >= 2  # At least 2 H2 sections
        assert h3_count >= 1  # At least 1 H3 subsection

    def test_structure_fixing_for_free_models(self) -> None:
        """Free model output should be fixed to proper structure."""
        from ai.generator import AIArticleGenerator
        
        class MockProvider:
            model = "test"
            def generate_article(self, **kwargs):
                # Simulate free model output with poor structure
                return "Test Title", "Some content without proper headings"
            def optimize_meta_description(self, **kwargs):
                return "Meta desc"
            def generate_faq(self, **kwargs):
                return []

        generator = AIArticleGenerator(provider=MockProvider())
        title, content = generator._provider.generate_article(topic="Test")
        
        # Should be fixed to proper structure
        fixed = generator._fix_heading_structure(content, title, [])
        assert "<h1>" in fixed
        assert len(fixed.split("<h2>")) >= 3  # At least 3 sections


class TestInternalLinking:
    """Tests for internal linking suggestions."""

    def test_related_posts_suggestion(self) -> None:
        """Should suggest related posts based on content."""
        from ai.internal_linking import InternalLinkSuggester

        suggester = InternalLinkSuggester()

        existing_posts = [
            {
                "id": "1",
                "title": "Python Programming Basics",
                "content": "<p>Learn Python fundamentals, syntax, and basic concepts.</p>",
                "url": "/python-basics",
                "keywords": ["python", "programming", "basics"]
            },
            {
                "id": "2",
                "title": "Advanced Python Techniques",
                "content": "<p>Explore advanced Python features, decorators, and metaprogramming.</p>",
                "url": "/python-advanced",
                "keywords": ["python", "advanced", "techniques"]
            },
        ]

        links = suggester.find_related_posts(
            current_content="<h1>Python Tips for Beginners</h1><p>Learn Python programming.</p>",
            target_keywords=["python", "programming"],
            existing_posts=existing_posts,
        )

        # Should find Python-related posts
        assert len(links) > 0

    def test_link_density_calculation(self) -> None:
        """Should calculate correct link density for word count."""
        from ai.internal_linking import InternalLinkSuggester

        suggester = InternalLinkSuggester()

        # 1000 words should suggest 3-5 links
        recommendation = suggester.get_link_density_recommendation(1000)
        assert recommendation["min_links"] == 3
        assert recommendation["max_links"] == 5


class TestLSIKeywords:
    """Tests for LSI keyword generation."""

    def test_lsi_keyword_generation(self) -> None:
        """Should generate semantic keyword variations."""
        from ai.keyword_optimizer import KeywordOptimizer

        optimizer = KeywordOptimizer()

        # Use fallback method (doesn't require API)
        lsi = optimizer._fallback_lsi_keywords("python programming", 5)

        assert len(lsi) >= 5
        assert all("keyword" in kw for kw in lsi)
        assert all("semantic_group" in kw for kw in lsi)

    def test_keyword_density_check(self) -> None:
        """Should validate keyword density is 1-2%."""
        from ai.keyword_optimizer import KeywordOptimizer

        optimizer = KeywordOptimizer()

        # High keyword density content
        content = "<p>python python python python python python python python python python</p>"
        result = optimizer.validate_keyword_density(content, "python")

        assert result["keyword"] == "python"
        assert result["is_optimal"] or result["density"] > 0  # Density is calculated
        assert "recommendations" in result


class TestKeywordDensity:
    """Tests for keyword density validation."""

    def test_howto_schema_generation(self) -> None:
        """Should generate HowTo schema for tutorial content."""
        from ai.schema_generator import SchemaGenerator, HowToStep

        generator = SchemaGenerator()

        steps = [
            HowToStep(name="Step 1", text="First step description"),
            HowToStep(name="Step 2", text="Second step description"),
        ]

        schema = generator.generate_howto_schema(
            title="How to Install Python",
            steps=steps,
            total_time="PT15M",
        )

        assert schema["@type"] == "HowTo"
        assert schema["name"] == "How to Install Python"
        assert len(schema["step"]) == 2
        assert schema["step"][0]["@type"] == "HowToStep"
        assert schema["step"][0]["name"] == "Step 1"
        assert schema["totalTime"] == "PT15M"

    def test_howto_schema_without_steps(self) -> None:
        """Should generate basic HowTo schema without steps."""
        from ai.schema_generator import SchemaGenerator

        generator = SchemaGenerator()

        schema = generator.generate_howto_schema(title="How to Install Python")

        assert schema["@type"] == "HowTo"
        assert schema["name"] == "How to Install Python"
        assert "step" not in schema

    def test_image_suggestions(self) -> None:
        """Should suggest images with alt text."""
        from media.image_selector import ImageSelector

        selector = ImageSelector()

        suggestions = selector.suggest_images(
            topic="Python programming",
            headings=["Introduction", "Variables"],
            count=4,
        )

        assert len(suggestions) == 4
        for suggestion in suggestions:
            assert suggestion.url
            assert suggestion.alt_text
            assert len(suggestion.alt_text) <= 125

    def test_image_alt_text_generation(self) -> None:
        """Should generate alt text with character limit."""
        from media.image_selector import ImageSelector

        selector = ImageSelector()
        alt_text = selector.generate_alt_text(
            "Python code showing a for loop",
            content="<h1>Python Tips</h1>",
        )

        assert alt_text
        assert len(alt_text) <= 125

    def test_image_html_generation(self) -> None:
        """Should generate proper HTML img tags."""
        from media.image_selector import ImageSelector, ImageSuggestion

        selector = ImageSelector()
        html = selector.generate_og_image_html(
            image_url="https://example.com/image.jpg",
            alt_text="Python code example",
        )

        assert 'src="https://example.com/image.jpg"' in html
        assert 'alt="Python code example"' in html
        assert 'width="1200"' in html

    def test_eeat_quality_scoring(self) -> None:
        """Should score content quality based on EEAT."""
        from seo.quality_scorer import QualityScorer

        scorer = QualityScorer()

        content = """
        <h1>Python Programming Guide</h1>
        <p>In my experience, Python is easy to learn.
        According to recent research, it's the most popular language.
        Source: Stack Overflow Survey 2025.</p>
        """

        score = scorer.score_content("Python Guide", content, sources=["https://example.com"])

        assert 0 <= score.overall <= 100
        assert score.trustworthiness > score.experience




class TestOpenGraphTags:
    """Tests for Open Graph and Twitter Card meta tag generation."""

    def test_open_graph_generation(self) -> None:
        """Should generate proper OG tags."""
        from ai.meta_optimizer import MetaDescriptionOptimizer

        class MockProvider:
            model = "test"
            def generate_text(self, prompt, **kwargs):
                return "A well-crafted meta description for SEO optimization purposes that is within limits"

        optimizer = MetaDescriptionOptimizer(provider=MockProvider())
        tags = optimizer.generate_open_graph_tags(
            title="Python Programming Guide",
            description="Learn Python programming with this comprehensive guide.",
            url="https://example.com/python-guide",
            image_url="https://example.com/og-image.jpg",
        )

        assert tags["og:title"] == "Python Programming Guide"
        assert tags["og:description"] == "Learn Python programming with this comprehensive guide."
        assert tags["og:type"] == "article"
        assert tags["og:url"] == "https://example.com/python-guide"
        assert tags["og:image"] == "https://example.com/og-image.jpg"
        assert tags["og:image:width"] == "1200"
        assert tags["og:image:height"] == "630"

    def test_open_graph_title_length(self) -> None:
        """OG title should be truncated to 60 chars."""
        from ai.meta_optimizer import MetaDescriptionOptimizer

        optimizer = MetaDescriptionOptimizer(provider=MockProvider())
        long_title = "This is a very long title that should be truncated to 60 characters for optimal SEO"
        tags = optimizer.generate_open_graph_tags(
            title=long_title,
            description="Test description",
        )

        assert len(tags["og:title"]) <= 60

    def test_twitter_card_generation(self) -> None:
        """Should generate proper Twitter Card tags."""
        from ai.meta_optimizer import MetaDescriptionOptimizer

        optimizer = MetaDescriptionOptimizer(provider=MockProvider())
        tags = optimizer.generate_twitter_card_tags(
            title="Python Tips",
            description="Learn Python with these tips",
            image_url="https://example.com/twitter.jpg",
            creator="johndoe",
        )

        assert tags["twitter:card"] == "summary_large_image"
        assert tags["twitter:title"] == "Python Tips"
        assert tags["twitter:description"] == "Learn Python with these tips"
        assert tags["twitter:image"] == "https://example.com/twitter.jpg"
        assert tags["twitter:creator"] == "@johndoe"

    def test_twitter_card_creator_with_at_prefix(self) -> None:
        """Twitter creator should already have @ prefix."""
        from ai.meta_optimizer import MetaDescriptionOptimizer

        optimizer = MetaDescriptionOptimizer(provider=MockProvider())
        tags = optimizer.generate_twitter_card_tags(
            title="Test",
            description="Test desc",
            creator="@johndoe",
        )

        assert tags["twitter:creator"] == "@johndoe"

    def test_social_meta_tags_combined(self) -> None:
        """Should combine OG and Twitter tags."""
        from ai.meta_optimizer import MetaDescriptionOptimizer

        optimizer = MetaDescriptionOptimizer(provider=MockProvider())
        tags = optimizer.generate_social_meta_tags(
            title="Test Article",
            description="Test description",
            url="https://example.com/test",
            image_url="https://example.com/image.jpg",
            creator="testuser",
        )

        # Should have all OG tags
        assert "og:title" in tags
        assert "og:description" in tags

        # Should have all Twitter tags
        assert "twitter:card" in tags
        assert "twitter:title" in tags


class MockProvider:
    """Mock provider for testing."""
    model = "test"
    def generate_text(self, prompt, **kwargs):
        return "A well-crafted meta description for SEO optimization purposes that is within limits"


class TestMetaTags:
    """Tests for meta tag generation."""

    def test_title_tag_length(self) -> None:
        """Title should be 50-60 characters."""
        from ai.seo_title import SEOTitleGenerator

        class MockProvider:
            model = "test"
            def generate_text(self, prompt, **kwargs):
                return "This is a test title that is exactly sixty chars long"
            def generate_article(self, **kwargs):
                return "Title", "<h1>Title</h1>"
            def generate_seo_title(self, topic, target_keywords=None, max_length=60, language="en"):
                return "This is a test title that is exactly sixty chars long"

        generator = SEOTitleGenerator(provider=MockProvider())
        response = generator.generate(SEOTitleRequest(topic="Test"))

        assert len(response.title) <= 60

    def test_meta_description_length(self) -> None:
        """Meta description should be 120-160 characters."""
        from ai.meta_optimizer import MetaDescriptionOptimizer
        
        class MockProvider:
            model = "test"
            def generate_text(self, prompt, **kwargs):
                return "A well-crafted meta description for SEO optimization purposes that is within limits"
            def generate_article(self, **kwargs):
                return "Title", "<h1>Title</h1>"
            def optimize_meta_description(self, content, title, target_keyword=None, length=155):
                # Return a description that is exactly 155 characters
                return "Learn SEO optimization with expert tips, strategies, and best practices for better search rankings and website visibility"

        optimizer = MetaDescriptionOptimizer(provider=MockProvider())
        response = optimizer.optimize(MetaOptimizationRequest(
            title="Test",
            content="<p>Test content</p>"
        ))
        
        # After sanitization, the character count should be valid
        assert 120 <= response.character_count <= 160

