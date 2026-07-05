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
        # Will be implemented in Phase 5
        pass


class TestLSIKeywords:
    """Tests for LSI keyword generation."""

    def test_lsi_keyword_generation(self) -> None:
        """Should generate semantic keyword variations."""
        # Will be implemented in Phase 5
        pass


class TestKeywordDensity:
    """Tests for keyword density validation."""

    def test_keyword_density_check(self) -> None:
        """Should validate keyword density is 1-2%."""
        # Will be implemented in Phase 5
        pass


class TestOpenGraphTags:
    """Tests for Open Graph meta tag generation."""

    def test_open_graph_generation(self) -> None:
        """Should generate proper OG tags."""
        # Will be implemented in Phase 5
        pass


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
            def generate_seo_title(self, topic, target_keywords=None, max_length=60):
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
            {
                "id": "3",
                "title": "SEO Optimization Guide",
                "content": "<p>Learn how to optimize content for search engines effectively.</p>",
                "url": "/seo-guide",
                "keywords": ["seo", "optimization", "search"]
            },
        ]

        links = suggester.find_related_posts(
            current_content="<h1>Python Tips for Beginners</h1><p>Learn Python programming with these tips for beginners starting their coding journey.</p>",
            target_keywords=["python", "programming", "beginners"],
            existing_posts=existing_posts,
        )

        # Should find Python-related posts
        assert len(links) > 0
        assert any("python" in link.anchor_text.lower() for link in links)

    def test_link_density_calculation(self) -> None:
        """Should calculate correct link density for word count."""
        from ai.internal_linking import InternalLinkSuggester

        suggester = InternalLinkSuggester()

        # 2500 words should suggest ~10 links (4 per 1000)
        recommendation = suggester.get_link_density_recommendation(2500)
        assert recommendation["min_links"] == 7  # 2500/1000 * 3 = 7.5 -> 7
        assert recommendation["max_links"] == 12  # 2500/1000 * 5 = 12.5 -> 12

    def test_anchor_text_generation(self) -> None:
        """Should generate keyword-rich anchor text."""
        from ai.internal_linking import InternalLinkSuggester

        suggester = InternalLinkSuggester()

        # Test with matching keywords
        anchor = suggester._generate_anchor_text(
            post_title="Python Programming Guide",
            post_keywords=["python", "programming", "guide"],
            current_keywords=["python", "seo"],
        )
        assert anchor.lower() == "python"

    def test_format_links_html(self) -> None:
        """Should format links as HTML."""
        from ai.internal_linking import InternalLinkSuggester, InternalLink

        suggester = InternalLinkSuggester()

        links = [
            InternalLink(
                post_id="1",
                post_title="Python Basics",
                url="/python-basics",
                anchor_text="Python",
                relevance_score=0.9,
                reason="Highly relevant"
            )
        ]

        html = suggester.format_links_html(links)
        assert "<h2>Further Reading</h2>" in html
        assert '<a href="/python-basics">Python</a>' in html
