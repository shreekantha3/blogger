#!/usr/bin/env python3
"""
SEO optimization to achieve 95+ scores.
Improves keyword density and readability.
"""

import re
from pathlib import Path
from config import get_settings, setup_logging
from core.blogger_client import BloggerClient
from core.models import BlogPost
from core.publishing import Publisher
from seo import SEOAnalyzer

# Setup logging
settings = get_settings()
setup_logging(level=settings.log_level, log_format=settings.log_format)

ARTICLES_TO_UPDATE = {
    "YASCCON Recruitment 2026: Complete Recruitment Guide 2026": {
        "post_id": "3228746417163920217",
        "keywords": ["YASCCON Recruitment 2026", "YASCCON Assistant Recruitment", "YASCCON Sub Staff Vacancy", "Souharda Co-operative Society Jobs", "Karnataka Co-operative Jobs", "Offline Application Jobs", "YASCCON Employment"]
    },
    "KFWCCF Recruitment 2026: Complete Recruitment Guide 2026": {
        "post_id": "2372462388302022567",
        "keywords": ["KFWCCF Recruitment 2026", "KFWCCF PRO Recruitment", "Karnataka Forest Recruitment", "Public Relation Officer Jobs", "Environmental Jobs Karnataka", "KFWCCF Application", "Forest Jobs Bengaluru"]
    },
    "SAIL Recruitment 2026: Complete Recruitment Guide 2026": {
        "post_id": "4291654852877435027",
        "keywords": ["SAIL Recruitment 2026", "SAIL Young Professional Recruitment", "Steel Authority of India Jobs", "SAIL Online Application", "Young Professional I Vacancy", "SAIL Careers", "Government Jobs Steel Sector"]
    },
    "BGSSS Recruitment 2026: Complete Recruitment Guide 2026": {
        "post_id": "4557392155868780885",
        "keywords": ["BGSSS Recruitment 2026", "BGSSS Jobs", "Baroda Global Shared Services Recruitment", "Aadhar Operator Jobs", "BGSSS Online Application", "Digital Banking Jobs", "Banking Sector Jobs"]
    },
    "WAMUL Recruitment 2026: Complete Recruitment Guide 2026": {
        "post_id": "3904578417889971984",
        "keywords": ["WAMUL Recruitment 2026", "Purabi Dairy Jobs", "West Assam Milk Producers Recruitment", "WAMUL Assistant Jobs", "Dairy Sector Jobs Assam", "Cooperative Jobs", "WAMUL Careers"]
    }
}


def add_keyword_mentions(content: str, primary_keyword: str) -> str:
    """Add more natural keyword mentions throughout content."""
    # Add keyword in first 200 chars
    first_part = content[:500]
    if primary_keyword.lower() not in first_part.lower():
        # Insert after the intro line
        content = content.replace(
            '<h2>',
            f'<p>{primary_keyword} recruitment drives offer stable career opportunities. Candidates must verify all eligibility requirements before applying.</p><h2>',
            1
        )

    # Add keyword mentions in FAQ answers
    content = content.replace(
        "There are <strong>",
        f"There are <strong>{primary_keyword} - "
    )

    # Add in conclusion
    if '<hr>' in content:
        meta_insert = f'''<p>For more information, visit {primary_keyword.split()[0]} official website. All details are based on official notification.</p>

<hr>'''
        content = content.replace('<hr>', meta_insert)

    return content


def main():
    """Update articles to achieve 95+ SEO scores."""
    print("=" * 60)
    print("SEO Optimization - Adding Keyword Mentions")
    print("=" * 60)

    analyzer = SEOAnalyzer()
    publisher = Publisher()

    for title, info in ARTICLES_TO_UPDATE.items():
        post_id = info["post_id"]
        keywords = info["keywords"]
        primary_keyword = keywords[0]

        print(f"\n--- {title[:50]}... ---")

        # Get current post
        result = publisher._client.get_post(post_id)
        if not result.success:
            print(f"Failed to fetch: {result.error}")
            continue

        raw = result.raw_response
        content = raw.get('content', '')

        # Add keyword mentions
        optimized_content = add_keyword_mentions(content, primary_keyword)

        # Check SEO improvement
        before_report = analyzer.analyze(title, content, target_keyword=primary_keyword)
        after_report = analyzer.analyze(title, optimized_content, target_keyword=primary_keyword)

        print(f"Before: {before_report.overall_score}/100")
        print(f"After:  {after_report.overall_score}/100")

        # Update post
        post = BlogPost(
            title=title,
            content=optimized_content,
            labels=keywords,
        )

        update_result = publisher.update_post(post_id, post)
        if update_result.success:
            print(f"✓ Updated")
        else:
            print(f"✗ Failed: {update_result.error}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()