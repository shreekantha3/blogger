"""
Utility helper functions.

ARCHITECTURAL DECISION: Why helpers module?
-------------------------------------------
This module follows the "Pure Functions" pattern:
1. Each function does one thing and does it well
2. No side effects - same input always produces same output
3. Easy to unit test in isolation
4. Can be moved to a shared library later if needed

These utilities are used across multiple modules to avoid duplication.

Uses BeautifulSoup for robust HTML parsing when available.
"""

import re
from typing import Optional

# Try to import BeautifulSoup for better HTML parsing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# For HTML entity decoding
try:
    import html as html_module
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False


def sanitize_html(content: str, allow_script: bool = False) -> str:
    """
    Sanitize HTML content by escaping/neutralizing dangerous elements.

    Args:
        content: Raw HTML content to sanitize
        allow_script: Whether to allow <script> tags (default: False)

    Returns:
        Sanitized HTML string

    Note:
        For production, consider using bleach or lxml for robust sanitization.
        This is a lightweight alternative for basic cases.

    Example:
        >>> sanitize_html("<script>alert('xss')</script><p>Hello</p>")
        "<p>Hello</p>"
    """
    if not content:
        return ""

    if BS4_AVAILABLE:
        return _sanitize_html_bs4(content, allow_script)

    # Fallback: If we're being strict, strip script tags
    if not allow_script:
        content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
        content = re.sub(r"<script[^>]*?>", "", content)
        content = content.replace("</script>", "")

    return content


def _sanitize_html_bs4(content: str, allow_script: bool = False) -> str:
    """Sanitize using BeautifulSoup."""
    soup = BeautifulSoup(content, 'html.parser')

    if not allow_script:
        for script in soup.find_all('script'):
            script.decompose()

    return str(soup)


def truncate_text(text: str, max_length: int = 160, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length for meta descriptions and titles.

    Args:
        text: Text to truncate
        max_length: Maximum length (default 160 for meta descriptions)
        suffix: Suffix to append if truncated

    Returns:
        Truncated text with suffix if it exceeded max_length

    Example:
        >>> truncate_text("This is a long title", max_length=10)
        "This is..."
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Account for suffix in truncation
    truncate_at = max_length - len(suffix)
    return text[:truncate_at].rstrip() + suffix


def slugify(text: str, separator: str = "-") -> str:
    """
    Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify
        separator: Character to use (default: -)

    Returns:
        Lowercase, hyphenated slug suitable for URLs

    Design decision:
        Simple slugification without external dependencies (like python-slugify).
        Covers common cases for blog post slugs. Can be enhanced in Phase 2.

    Example:
        >>> slugify("Hello World! This is a Post")
        "hello-world-this-is-a-post"
    """
    if not text:
        return ""

    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and underscores with separator
    slug = re.sub(r"[\s_]+", separator, slug)

    # Remove special characters except separator
    slug = re.sub(r"[^a-z0-9\-]", "", slug)

    # Remove multiple consecutive separators
    slug = re.sub(r"-{2,}", separator, slug)

    # Strip leading/trailing separators
    slug = slug.strip(separator)

    return slug


def extract_text_from_html(html_content: str) -> str:
    """
    Extract plain text from HTML content.

    Uses BeautifulSoup when available for robust parsing,
    falls back to regex for basic cases.

    Useful for SEO analysis, summary generation, and readability checks.

    Args:
        html_content: HTML to extract text from

    Returns:
        Plain text with tags removed

    Example:
        >>> extract_text_from_html("<p>Hello <strong>world</strong></p>")
        "Hello world"
    """
    if not html_content:
        return ""

    if BS4_AVAILABLE:
        return _extract_text_bs4(html_content)

    return _extract_text_regex(html_content)


def _extract_text_bs4(html_content: str) -> str:
    """Extract text using BeautifulSoup."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ')
    return re.sub(r'\s+', ' ', text).strip()


def _extract_text_regex(html_content: str) -> str:
    """Extract text using regex (fallback)."""
    # Simple HTML tag removal
    text = re.sub(r"<[^>]+>", " ", html_content)

    # Decode HTML entities
    if HTML_AVAILABLE:
        text = html_module.unescape(text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text