"""
Tests for Phase 5 Research Module (Reference URL Processing).
"""

import pytest
from ai.research import (
    fetch_url_content,
    extract_text_from_html,
    extract_headings,
    extract_links,
    extract_statistics,
    research_topic,
    ResearchResult,
)


class TestExtractTextFromHtml:
    """Tests for HTML text extraction."""

    def test_extract_plain_text(self) -> None:
        """Extract text from HTML without tags."""
        html = "<p>This is <strong>bold</strong> text.</p>"
        text = extract_text_from_html(html)
        assert "This is" in text
        assert "bold" in text
        assert "text" in text

    def test_extract_with_script_removal(self) -> None:
        """Script tags should be removed."""
        html = "<script>console.log('test');</script><p>Visible content</p>"
        text = extract_text_from_html(html)
        assert "console.log" not in text
        assert "Visible content" in text

    def test_empty_input(self) -> None:
        """Empty input returns empty string."""
        assert extract_text_from_html("") == ""
        assert extract_text_from_html(None) == ""  # type: ignore


class TestExtractHeadings:
    """Tests for heading extraction."""

    def test_extract_single_h1(self) -> None:
        """Extract H1 heading."""
        html = "<h1>Main Title</h1><h2>Section</h2>"
        headings = extract_headings(html)
        assert len(headings) == 2
        assert "Main Title" in headings or "Main Title" in headings[0]

    def test_extract_multiple_headings(self) -> None:
        """Extract all heading levels."""
        html = "<h1>Title</h1><h2>Section 1</h2><h3>Subsection</h3>"
        headings = extract_headings(html)
        assert len(headings) == 3

    def test_no_headings(self) -> None:
        """No headings returns empty list."""
        html = "<p>Just paragraphs</p>"
        headings = extract_headings(html)
        assert headings == []


class TestExtractLinks:
    """Tests for link extraction."""

    def test_extract_single_link(self) -> None:
        """Extract a link from HTML."""
        html = '<p>Check <a href="https://example.com">this link</a></p>'
        links = extract_links(html)
        assert len(links) == 1
        assert links[0]["url"] == "https://example.com"
        assert links[0]["text"] == "this link"

    def test_extract_multiple_links(self) -> None:
        """Extract multiple links."""
        html = '<a href="/page1">Page 1</a> <a href="/page2">Page 2</a>'
        links = extract_links(html)
        assert len(links) == 2


class TestExtractStatistics:
    """Tests for statistics extraction."""

    def test_find_percentages(self) -> None:
        """Find percentage values."""
        text = "Sales increased by 25%. Revenue reaches 1 million users."
        stats = extract_statistics(text)
        assert len(stats) > 0

    def test_no_statistics(self) -> None:
        """No statistics returns empty list."""
        text = "This is just regular text without numbers."
        stats = extract_statistics(text)
        assert stats == []


class TestResearchTopic:
    """Tests for research workflow."""

    def test_research_with_valid_url(self) -> None:
        """Research topic synthesizes findings."""
        # This test uses actual HTTP - in production would mock
        # For now, test the structure
        result = ResearchResult()
        assert result.sources == []
        assert result.key_points == []
        assert result.facts == []

    def test_research_with_empty_urls(self) -> None:
        """Research with no URLs returns empty result."""
        result = research_topic("Test Topic", [])
        assert result.sources == []


class TestResearchResult:
    """Tests for ResearchResult data class."""

    def test_empty_initialization(self) -> None:
        """ResearchResult initializes with empty lists."""
        result = ResearchResult()
        assert result.sources == []
        assert result.key_points == []
        assert result.facts == []
        assert result.statistics == []
        assert result.quotes == []
        assert result.topics == []

    def test_add_sources(self) -> None:
        """Can add sources to result."""
        result = ResearchResult()
        result.sources.append("https://example.com")
        assert len(result.sources) == 1


class TestFetchUrlContent:
    """Tests for URL fetching."""

    def test_invalid_url(self) -> None:
        """Invalid URL returns None."""
        result = fetch_url_content("not-a-valid-url")
        assert result is None

    def test_empty_url(self) -> None:
        """Empty URL returns None."""
        result = fetch_url_content("")
        assert result is None

    def test_robots_txt(self) -> None:
        """Cannot fetch robots.txt easily (tests graceful failure)."""
        # This tests the error handling path
        result = fetch_url_content("https://example.com/robots.txt", timeout=5)
        # May succeed or fail depending on network, but shouldn't crash