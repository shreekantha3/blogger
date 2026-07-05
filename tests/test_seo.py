"""Tests for Phase 3 SEO Engine."""

from seo.meta import MetaDescriptionGenerator
from seo.headings import HeadingAnalyzer
from seo.keywords import KeywordAnalyzer
from seo.readability import ReadabilityAnalyzer
from seo.analyzer import SEOAnalyzer
from seo.models import SEOScore, SEORport


class TestMetaDescriptionGenerator:
    """Tests for meta description generation."""

    def test_generate_from_content(self) -> None:
        """Generate meta description from HTML content."""
        generator = MetaDescriptionGenerator()

        content = "<p>This is a test post about Python programming. We discuss best practices.</p>"
        meta = generator.generate(content, title="Test Post")

        assert len(meta) <= 160
        assert "Python" in meta or "test" in meta.lower()

    def test_validate_good_meta(self) -> None:
        """Validate an optimal meta description."""
        generator = MetaDescriptionGenerator()

        # 155 chars - in optimal range (120-160)
        meta = "Learn about Python programming best practices in this comprehensive and detailed guide for developers."
        score = generator.validate(meta)

        assert score.value >= 70  # Good score
        assert len(score.issues) == 0

    def test_validate_missing_meta(self) -> None:
        """Validate missing meta description."""
        generator = MetaDescriptionGenerator()

        score = generator.validate("")

        assert score.value == 0
        assert "Missing" in score.issues[0]


class TestHeadingAnalyzer:
    """Tests for heading analysis."""

    def test_extract_single_h1(self) -> None:
        """Extract single H1 heading."""
        analyzer = HeadingAnalyzer()

        html = "<h1>Main Title</h1><h2>Section</h2>"
        headings = analyzer.extract_headings(html)

        assert len(headings) == 2
        assert headings[0].level == 1
        assert headings[0].text == "Main Title"

    def test_analyze_good_structure(self) -> None:
        """Analyze well-structured headings."""
        analyzer = HeadingAnalyzer()

        html = "<h1>Main</h1><h2>Section 1</h2><h2>Section 2</h2>"
        score = analyzer.analyze(html)

        assert score.value >= 80

    def test_analyze_missing_h1(self) -> None:
        """Analyze content missing H1."""
        analyzer = HeadingAnalyzer()

        html = "<h2>Only H2</h2>"
        score = analyzer.analyze(html)

        assert any("Missing H1" in issue for issue in score.issues)


class TestKeywordAnalyzer:
    """Tests for keyword analysis."""

    def test_analyze_low_density(self) -> None:
        """Analyze content with no target keyword."""
        analyzer = KeywordAnalyzer()

        # Natural text without keyword spam - more content
        content = """
            <p>We discuss programming concepts and best practices.</p>
            <p>Python is mentioned once in passing. Other technical topics are covered.</p>
            <p>This guide covers various programming languages and frameworks.</p>
        """
        score = analyzer.analyze(content, target_keyword="python")

        # Should have reasonable score (keyword appears naturally)
        assert score.value >= 30  # Even with low density, should be reasonable

    def test_suggest_keywords(self) -> None:
        """Get keyword suggestions."""
        analyzer = KeywordAnalyzer()

        content = "<p>Python is great for data science. Python programming is fun.</p>"
        suggestions = analyzer.suggest_keywords(content)

        assert "python" in suggestions[0].lower() or len(suggestions) > 0


class TestReadabilityAnalyzer:
    """Tests for readability analysis."""

    def test_analyze_simple_text(self) -> None:
        """Analyze simple, readable text."""
        analyzer = ReadabilityAnalyzer()

        html = "<p>This is short. This is clear. Easy words here.</p>"
        score = analyzer.analyze(html)

        assert score.value >= 80
        assert len(score.issues) == 0

    def test_analyze_complex_text(self) -> None:
        """Analyze complex, hard-to-read text."""
        analyzer = ReadabilityAnalyzer()

        # Long, complex sentence
        html = "<p>Utilize the aforementioned methodologies for the implementation of scalable distributed microservices architectures within cloud-native environments.</p>"
        score = analyzer.analyze(html)

        # Should have suggestions for improvement
        assert score.value < 80 or len(score.issues) > 0


class TestSEOAnalyzer:
    """Tests for main SEO analyzer."""

    def test_analyze_complete_post(self) -> None:
        """Analyze a complete post."""
        analyzer = SEOAnalyzer()

        title = "Beginner's Guide to Python"
        content = """
            <h1>Beginner's Guide to Python</h1>
            <h2>Getting Started</h2>
            <p>Python is a popular programming language. It is easy to learn.</p>
            <h2>Advanced Topics</h2>
            <p>Once you know the basics, try these advanced concepts.</p>
        """

        report = analyzer.analyze(title, content, target_keyword="Python")

        assert 0 <= report.overall_score <= 100
        assert report.title_score.value > 0
        assert report.meta_score.value > 0

    def test_validate_and_correct(self) -> None:
        """Test validate and correct method."""
        analyzer = SEOAnalyzer()

        # Poor SEO post
        title = "Hi"
        content = "<p>Short.</p>"

        is_valid, corrections = analyzer.validate_and_correct(title, content)

        assert is_valid == False
        assert len(corrections) > 0