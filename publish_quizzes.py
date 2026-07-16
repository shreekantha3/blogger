#!/usr/bin/env python3
"""
Batch publish quiz pages to Blogger.

Run this script AFTER authenticating with:
    python3 app.py auth

Usage:
    python3 publish_quizzes.py
"""

import json
from pathlib import Path
from config import get_settings, setup_logging, get_logger
from core.blogger_client import BloggerClient
from core.models import BlogPost
from core.publishing import Publisher

# Quiz configuration
QUIZZES = [
    {
        "file": "indian-constitutional-amendments-essentials-quiz.html",
        "title": "Indian Constitutional Amendments Quiz: Master 25 Essential MCQs for Competitive Exams",
        "labels": ["quiz", "constitutional amendments", "kpsc", "upsc", "polity"]
    },
    {
        "file": "fundamental-rights-india-quiz.html",
        "title": "Fundamental Rights Quiz: Master 25 Essential MCQs for Competitive Exams",
        "labels": ["quiz", "fundamental rights", "kpsc", "upsc", "polity"]
    },
    {
        "file": "directive-principles-india-quiz.html",
        "title": "Directive Principles Quiz: Master 25 Essential MCQs for Competitive Exams",
        "labels": ["quiz", "directive principles", "kpsc", "upsc", "polity"]
    },
    {
        "file": "presidents-rule-article-356-quiz.html",
        "title": "President's Rule (Article 356) Quiz: Master 25 Essential MCQs",
        "labels": ["quiz", "presidents rule", "kpsc", "upsc", "polity", "federal structure"]
    },
    {
        "file": "panchayati-raj-73rd-amendment-quiz.html",
        "title": "Panchayati Raj Quiz: Master 25 Essential MCQs on 73rd Amendment",
        "labels": ["quiz", "panchayati raj", "kpsc", "upsc", "local governance"]
    },
    {
        "file": "emergency-provisions-india-quiz.html",
        "title": "Emergency Provisions Quiz: Master 25 Essential MCQs",
        "labels": ["quiz", "emergency provisions", "kpsc", "upsc", "polity"]
    }
]

def publish_quizzes():
    """Publish all quiz pages to Blogger."""
    settings = get_settings()
    setup_logging(level=settings.log_level)
    logger = get_logger("publish_quizzes")

    articles_dir = Path("articles")

    print(f"Publishing {len(QUIZZES)} quiz pages to Blogger...")
    print(f"Target blog ID: {settings.blogger_blog_id}\n")

    success_count = 0

    for quiz in QUIZZES:
        html_file = articles_dir / quiz["file"]

        if not html_file.exists():
            print(f"✗ File not found: {quiz['file']}")
            continue

        # Read HTML content
        content = html_file.read_text()

        print(f"Publishing: {quiz['title'][:50]}...")

        # Create post
        post = BlogPost(
            title=quiz["title"],
            content=content,
            labels=quiz["labels"]
        )

        # Publish
        try:
            publisher = Publisher()
            result = publisher.publish(post)

            if result.success:
                print(f"  ✓ Published successfully!")
                print(f"    Post ID: {result.post_id}")
                print(f"    URL: {result.url}\n")
                success_count += 1
            else:
                print(f"  ✗ Failed: {result.error}\n")

        except Exception as e:
            print(f"  ✗ Error: {e}\n")

    print(f"\n{'='*50}")
    print(f"Publishing complete: {success_count}/{len(QUIZZES)} successful")

    return success_count == len(QUIZZES)

if __name__ == "__main__":
    import sys
    success = publish_quizzes()
    sys.exit(0 if success else 1)