#!/usr/bin/env python3
"""
Publish recruitment articles to Blogger.

This script publishes the optimized recruitment articles to the configured Blogger blog.
SEO-optimized content is read from articles_optimized/ directory and published.
"""

from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.blogger_client import BloggerClient
from core.models import BlogPost
from core.auth import Authenticator
from config import get_settings, setup_logging, get_logger


def extract_title(content: str) -> str:
    """Extract title from HTML content (first H1 tag)."""
    import re
    match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    return match.group(1).strip() if match else "Untitled"


def extract_keywords(content: str) -> list[str]:
    """Extract keywords from content meta."""
    import re
    match = re.search(r'<strong>Keywords:</strong>\s*(.*?)(?:</p>|$)', content, re.DOTALL | re.IGNORECASE)
    if match:
        keywords_str = match.group(1)
        keywords = [k.strip() for k in keywords_str.split(',')]
        return keywords[:5]  # Limit to 5 for Blogger labels
    return []


def publish_articles():
    """Publish all recruitment articles from articles_optimized directory."""
    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        log_file_path=settings.log_file_path,
    )
    logger = get_logger("scripts", "publish_recruitment")

    optimized_dir = Path("articles_optimized")
    if not optimized_dir.exists():
        print("✗ articles_optimized directory not found")
        return

    # Find all recruitment articles
    articles = list(optimized_dir.glob("*recruitment*.html"))
    # Also check for specific topic files
    articles.extend(optimized_dir.glob("*karnataka-excise*.html"))
    articles.extend(optimized_dir.glob("*aiims*.html"))
    articles.extend(optimized_dir.glob("*tmb*.html"))
    articles.extend(optimized_dir.glob("*nhsrcl*.html"))
    articles.extend(optimized_dir.glob("*cotton*.html"))

    # Remove duplicates
    articles = list(set(articles))

    print(f"Found {len(articles)} recruitment articles to publish:\n")

    client = None

    for article_path in sorted(articles):
        print(f"Processing: {article_path.name}")

        try:
            content = article_path.read_text()
            title = extract_title(content)
            labels = extract_keywords(content)

            # Ensure recruitment label
            if 'recruitment' not in labels:
                labels.append('recruitment')
            if '2026' not in labels and '2025' not in labels:
                labels.append('jobs')

            post = BlogPost(
                title=title,
                content=content,
                labels=labels,
            )

            if client is None:
                client = BloggerClient()

            result = client.publish_post(post)

            if result.success:
                print(f"  ✓ Published: {result.url}")
                # Save mapping
                published_dir = Path("articles_converted")
                published_dir.mkdir(exist_ok=True)
                (published_dir / f"{article_path.stem}.json").write_text(f'{{"url": "{result.url}", "post_id": "{result.post_id}"}}')
            else:
                print(f"  ✗ Failed: {result.error}")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\nPublishing complete!")


if __name__ == "__main__":
    publish_articles()