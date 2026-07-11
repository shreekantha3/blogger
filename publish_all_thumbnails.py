#!/usr/bin/env python3
"""Publish all recruitment articles with Unsplash thumbnails.

Note: Uses Unsplash source URLs which Blogger fetches automatically.
For custom texture thumbnails, use --background flag with the thumbnail command.
"""

import json
from pathlib import Path
from core.publishing import Publisher
from core.models import BlogPost

# Load all articles and publish with thumbnails
articles_dir = Path("/Users/shree/Desktop/blogger/articles")
articles = [
    "aiims-gorakhpur-recruitment-2026-junior-resident.html",
    "cotton-corporation-of-india-recruitment-2026.html",
    "karnataka-excise-department-recruitment-2025.html",
    "nhsrcl-recruitment-2026-technician-junior-engineer.html",
    "tmb-recruitment-2026-senior-relationship-manager.html",
]

labels_map = {
    "aiims": ["recruitment", "medical", "aiims", "gorakhpur"],
    "cotton": ["recruitment", "corporate", "india", "jobs"],
    "karnataka": ["recruitment", "excise", "karnataka", "government"],
    "nhsrcl": ["recruitment", "infrastructure", "highway", "jobs"],
    "tmb": ["recruitment", "banking", "tmb", "jobs"],
}

publisher = Publisher()

for article in articles:
    if not articles_dir.exists():
        continue

    article_path = articles_dir / article
    if not article_path.exists():
        continue

    # Extract title from H1 tag
    content = article_path.read_text()
    if content.startswith("<h1>"):
        title_end = content.find("</h1>")
        title = content[4:title_end]
    else:
        title = article.replace(".html", "").replace("-", " ").title()

    # Determine labels from filename
    name = article.lower()
    labels = labels_map.get(name.split("-")[0], ["recruitment"])

    # Create post and publish with thumbnail
    post = BlogPost(title=title, content=content, labels=labels)

    print(f"Publishing: {title}...")
    result = publisher.publish(post, thumbnail=True)

    if result.success:
        print(f"  ✓ Published! URL: {result.url}")
    else:
        print(f"  ✗ Failed: {result.error}")

print("\nDone!")