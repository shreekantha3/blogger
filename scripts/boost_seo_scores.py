#!/usr/bin/env python3
"""
Boost SEO scores to 95+ by updating existing published articles.
"""

import re
from pathlib import Path
from config import get_settings, setup_logging
from core.blogger_client import BloggerClient
from core.models import BlogPost
from core.publishing import Publisher
from seo import SEOAnalyzer

settings = get_settings()
setup_logging(level=settings.log_level)

# Existing published articles with post IDs
ARTICLES = {
    "YASCCON Recruitment 2026: Complete Recruitment Guide 2026 - Apply Before Last Date": {
        "post_id": "3228746417163920217",
        "keywords": ["YASCCON Recruitment 2026", "YASCCON Assistant Recruitment", "YASCCON Sub Staff Vacancy", "Souharda Co-operative Society Jobs", "Karnataka Co-operative Jobs", "Offline Application Jobs", "YASCCON Employment"]
    },
    "KFWCCF Recruitment 2026: Complete Recruitment Guide 2026 - Apply Before Last Date": {
        "post_id": "2372462388302022567",
        "keywords": ["KFWCCF Recruitment 2026", "KFWCCF PRO Recruitment", "Karnataka Forest Recruitment", "Public Relation Officer Jobs", "Environmental Jobs Karnataka", "KFWCCF Application", "Forest Jobs Bengaluru"]
    },
    "SAIL Recruitment 2026: Complete Recruitment Guide 2026 - Apply Before Last Date": {
        "post_id": "4291654852877435027",
        "keywords": ["SAIL Recruitment 2026", "SAIL Young Professional Recruitment", "Steel Authority of India Jobs", "SAIL Online Application", "Young Professional I Vacancy", "SAIL Careers", "Government Jobs Steel Sector"]
    },
    "BGSSS Recruitment 2026: Complete Recruitment Guide 2026 - Apply Before Last Date": {
        "post_id": "4557392155868780885",
        "keywords": ["BGSSS Recruitment 2026", "BGSSS Jobs", "Baroda Global Shared Services Recruitment", "Aadhar Operator Jobs", "BGSSS Online Application", "Digital Banking Jobs", "Banking Sector Jobs"]
    },
    "WAMUL Recruitment 2026: Complete Recruitment Guide 2026 - Apply Before Last Date": {
        "post_id": "3904578417889971984",
        "keywords": ["WAMUL Recruitment 2026", "Purabi Dairy Jobs", "West Assam Milk Producers Recruitment", "WAMUL Assistant Jobs", "Dairy Sector Jobs Assam", "Cooperative Jobs", "WAMUL Careers"]
    }
}


def optimize_content(content: str, primary_keyword: str) -> str:
    """Optimize content for better SEO scores."""

    # Add keyword in first 100 words
    first_h2 = content.find('<h2>')
    if first_h2 != -1:
        keyword_para = f'<p>{primary_keyword} offers good jobs. See all details below.</p>\n'
        content = content[:first_h2] + keyword_para + content[first_h2:]

    # Add keyword mentions throughout
    content = content.replace(
        'candidates should apply',
        f'candidates should apply for {primary_keyword}'
    )

    # Add in FAQ answers
    content = content.replace(
        'There are <strong>',
        f'There are <strong>{primary_keyword} post vacancy: <strong>'
    )

    return content


def main():
    """Update articles for better SEO."""
    print("=" * 60)
    print("Boosting SEO Scores for Published Articles")
    print("=" * 60)

    client = BloggerClient()
    publisher = Publisher()
    analyzer = SEOAnalyzer()

    for title, info in ARTICLES.items():
        post_id = info["post_id"]
        keywords = info["keywords"]
        primary = keywords[0]

        print(f"\n--- {title[:40]}... ---")

        # Get current post
        result = client.get_post(post_id)
        if not result.success:
            print(f"Failed: {result.error}")
            continue

        raw = result.raw_response
        content = raw.get('content', '')
        labels = raw.get('labels', keywords)

        # Optimize
        opt_content = optimize_content(content, primary)

        # Check scores
        before = analyzer.analyze(title, content, target_keyword=primary).overall_score
        after = analyzer.analyze(title, opt_content, target_keyword=primary).overall_score
        print(f"Score: {before} -> {after}")

        # Update
        post = BlogPost(title=title, content=opt_content, labels=labels)
        update = publisher.update_post(post_id, post)

        if update.success:
            print("✓ Updated")
        else:
            print(f"✗ Failed: {update.error}")

    print("\nDone!")


if __name__ == "__main__":
    main()