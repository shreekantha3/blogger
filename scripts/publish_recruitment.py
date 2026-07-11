#!/usr/bin/env python3
"""
Publish recruitment articles to Blogger.
Uses Publisher for proper retry handling and logging.
"""

from pathlib import Path
import re
import sys

# Ensure worktree is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings, setup_logging
from core.models import BlogPost
from core.publishing import Publisher


def extract_metadata(content: str) -> tuple[str, list[str]]:
    """Extract title and keywords from HTML content."""
    # Extract title from H1
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Untitled"

    # Extract keywords from the end
    keywords_match = re.search(r'<strong>keywords:</strong>\s*(.*?)(?:</p>|$)', content, re.DOTALL | re.IGNORECASE)
    if keywords_match:
        keywords_str = keywords_match.group(1)
        keywords = [k.strip() for k in keywords_str.split(',')]
    else:
        # Derive from title
        keywords = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*\b', title)

    # Clean and limit keywords
    keywords = keywords[:5]
    if 'recruitment' not in keywords:
        keywords.append('recruitment')
    if '2026' in title and '2026' not in keywords:
        keywords.append('2026')
    if '2025' in title and '2025' not in keywords:
        keywords.append('2025')

    return title, keywords


def publish_recruitment_articles():
    """Publish all recruitment articles to Blogger."""
    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        log_file_path=settings.log_file_path,
    )

    optimized_dir = Path("articles_optimized")
    if not optimized_dir.exists():
        print("✗ articles_optimized directory not found")
        return

    # Find recruitment articles
    articles = [
        "karnataka-excise-department-recruitment-2025.html",
        "aiims-gorakhpur-recruitment-2026-junior-resident.html",
        "tmb-recruitment-2026-senior-relationship-manager.html",
        "nhsrcl-recruitment-2026-technician-junior-engineer.html",
        "cotton-corporation-of-india-recruitment-2026.html",
    ]

    publisher = Publisher()
    published = []
    failed = []

    print(f"\n{'='*60}")
    print("Publishing Recruitment Articles to Blogger")
    print(f"{'='*60}\n")

    for article_name in articles:
        article_path = optimized_dir / article_name
        if not article_path.exists():
            print(f"⚠ Skipping {article_name} - not found")
            continue

        content = article_path.read_text()
        title, labels = extract_metadata(content)

        print(f"Publishing: {title[:50]}...")

        post = BlogPost(
            title=title,
            content=content,
            labels=labels,
        )

        try:
            result = publisher.publish(post)
            if result.success:
                print(f"  ✓ Success: {result.url}")
                published.append({"title": title, "url": result.url})
            else:
                print(f"  ✗ Failed: {result.error}")
                failed.append({"title": title, "error": result.error})
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed.append({"title": title, "error": str(e)})

    print(f"\n{'='*60}")
    print(f"Results: {len(published)} published, {len(failed)} failed")
    print(f"{'='*60}\n")

    for p in published:
        print(f"  ✓ {p['title'][:40]}")
        print(f"    {p['url']}")

    return published, failed


if __name__ == "__main__":
    publish_recruitment_articles()