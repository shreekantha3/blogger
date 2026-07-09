"""
Research Module for Reference URL Processing.

ARCHITECTURAL DECISION: Research-Enriched Content Generation
--------------------------------------------------------------
This module implements the core vision feature: providing reference URLs
to generate more accurate, fact-checked content.

Workflow:
1. Fetch content from URLs
2. Extract text and key information
3. Generate structured knowledge from sources
4. Use insights to inform article generation
"""

import re
from typing import Optional
from urllib.parse import urlparse

import httpx
from config import get_logger

logger = get_logger("ai", "research")


class ResearchResult:
    """
    Structured research findings from reference URLs.

    Attributes:
        sources: List of source URLs
        key_points: Extracted key points
        facts: Verified facts with sources
        statistics: Numerical data found
        quotes: Direct quotes with attribution
        topics: Related topics discovered
    """

    def __init__(self) -> None:
        self.sources: list[str] = []
        self.key_points: list[str] = []
        self.facts: list[dict[str, str]] = []
        self.statistics: list[dict[str, str]] = []
        self.quotes: list[dict[str, str]] = []
        self.topics: list[str] = []


def fetch_url_content(url: str, timeout: int = 30) -> Optional[str]:
    """
    Fetch content from a URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content or None if failed

    Raises:
        ValueError: If URL is invalid
    """
    if not url or not url.strip():
        return None

    # Validate URL format
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        logger.warning("Invalid URL format", url=url)
        return None

    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        logger.error("Failed to fetch URL", url=url, error=str(e))
        return None


def extract_text_from_html(html: str) -> str:
    """
    Extract clean text from HTML content.

    Uses BeautifulSoup-style regex for simplicity.
    For production, consider using beautifulsoup4.

    Args:
        html: HTML content to extract from

    Returns:
        Clean text with minimal formatting
    """
    if not html:
        return ""

    # Remove script and style tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Decode common HTML entities
    entity_map = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
    }
    for entity, char in entity_map.items():
        text = text.replace(entity, char)

    return text


def extract_headings(html: str) -> list[str]:
    """
    Extract headings from HTML content.

    Args:
        html: HTML content

    Returns:
        List of heading texts (H1-H6)
    """
    headings = []
    for level in range(1, 7):
        pattern = rf"<h{level}[^>]*>(.*?)</h{level}>"
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        for match in matches:
            text = re.sub(r'<[^>]+>', '', match).strip()
            if text:
                headings.append(text)
    return headings


def extract_links(html: str) -> list[dict[str, str]]:
    """
    Extract links from HTML content.

    Args:
        html: HTML content

    Returns:
        List of dicts with 'url' and 'text' keys
    """
    links = []
    pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

    for url, text in matches:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if clean_text and url:
            links.append({'url': url, 'text': clean_text})

    return links


def extract_images(html: str) -> list[dict[str, str]]:
    """
    Extract image information from HTML content.

    Args:
        html: HTML content

    Returns:
        List of dicts with 'url', 'alt', and 'caption' keys
    """
    images = []
    pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\']'

    for match in re.finditer(pattern, html, re.IGNORECASE):
        images.append({
            'url': match.group(1),
            'alt': match.group(2),
            'caption': '',
        })

    return images


def extract_statistics(text: str) -> list[dict[str, str]]:
    """
    Extract statistical claims from text.

    Looks for patterns like "X%" or "X out of Y" or numerical data.

    Args:
        text: Plain text

    Returns:
        List of statistics found
    """
    stats = []

    # Pattern for percentages and numbers
    patterns = [
        r'(\d+(?:\.\d+)?%)\s*(.+?)(?:\.|$)',
        r'(\d+(?:\.\d+)?(?:\s*(?:million|billion|thousand)))\s*(.+?)(?:\.|$)',
        r'(increased?|decreased?|rose|fell)\s*(?:by\s*)?(\d+(?:\.\d+)?%?)(?:\s+(?:to|from)\s+(.+?))?(?:\.|$)',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            stats.append({
                'value': match.group(0),
                'context': match.group(0),
            })

    return stats


def research_topic(topic: str, reference_urls: list[str]) -> ResearchResult:
    """
    Research a topic using reference URLs.

    Main entry point for reference-based article generation.

    Args:
        topic: Main topic to research
        reference_urls: URLs to use as sources

    Returns:
        ResearchResult with extracted information

    Example:
        >>> result = research_topic(
        ...     "Python programming",
        ...     ["https://python.org/about", "https://wikipedia.org/wiki/Python"]
        ... )
        >>> len(result.key_points) > 0
    """
    result = ResearchResult()

    for url in reference_urls:
        logger.info("Researching URL", url=url)

        html = fetch_url_content(url)
        if not html:
            continue

        result.sources.append(url)
        text = extract_text_from_html(html)

        # Extract headings (indicates content structure)
        headings = extract_headings(html)
        for heading in headings[:10]:
            result.topics.append(heading)

        # Extract links (may indicate related topics)
        links = extract_links(html)
        for link in links[:5]:
            if link['url'] not in result.sources:
                result.sources.append(link['url'])

        # Extract statistics
        stats = extract_statistics(text)
        result.statistics.extend(stats[:5])

    logger.info(
        "Research complete",
        topic=topic[:50],
        sources_found=len(result.sources),
        topics_found=len(result.topics),
    )

    return result


def synthesize_research(research: ResearchResult, topic: str, max_length: int = 500) -> str:
    """
    Synthesize research findings into a summary.

    Args:
        research: Research findings
        topic: Topic for context
        max_length: Maximum length of synthesis

    Returns:
        Synthesized summary text
    """
    if not research.sources:
        return ""

    parts = [f"Based on research from {len(research.sources)} sources:"]
    parts.append(f"\nKey topics identified: {', '.join(research.topics[:5])}")

    if research.statistics:
        parts.append(f"\nStatistical highlights: {len(research.statistics)} data points found")

    synthesis = " ".join(parts)
    return synthesis[:max_length]