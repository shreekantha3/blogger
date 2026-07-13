#!/usr/bin/env python3
"""
Update existing articles to achieve 95+ SEO score.
"""

import re
from pathlib import Path
from config import get_settings, setup_logging
from core.blogger_client import BloggerClient
from core.models import BlogPost
from seo import SEOAnalyzer

# Setup logging
settings = get_settings()
setup_logging(level=settings.log_level, log_format=settings.log_format)

# Article data with post IDs
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


def optimize_title(title: str, keywords: list[str]) -> str:
    """Optimize title for 50-70 characters and keyword inclusion."""
    # Remove trailing incomplete text
    if title.endswith("..."):
        title = title[:-3]

    if len(title) < 50:
        # Add keywords to extend title
        extended = f"{title}: Eligibility, Salary, Selection Process for {keywords[0]}"
        if len(extended) > 70:
            extended = f"{title}: Complete 2026 Recruitment Guide"
        return extended[:70]
    elif len(title) > 70:
        return title[:67] + "..."
    return title


def optimize_content(content: str, title: str, keywords: list[str]) -> str:
    """Optimize content for better keyword density and SEO."""
    # Ensure target keywords appear more frequently in first 500 chars
    primary_keyword = keywords[0]

    # Add keyword mention in the first section if missing
    first_500 = content[:500]
    if primary_keyword.lower() not in first_500.lower():
        # Insert after intro paragraph
        content = re.sub(
            r'<h2>(.*?)<\/h2>',
            f'<h2>\\1</h2>\n<p><strong>{primary_keyword}</strong> - This recruitment provides excellent career opportunities with job security and growth prospects. All eligible candidates should apply before the last date to secure their application.</p>',
            content,
            count=1
        )

    # Add more keyword mentions throughout
    # Count keyword occurrences
    keyword_count = content.lower().count(primary_keyword.lower())

    # If keyword density is low, add more mentions
    if keyword_count < 5:
        # Add in FAQ answers
        content = content.replace(
            "candidates should apply",
            f"candidates for {primary_keyword} should apply"
        )
        content = content.replace(
            "for candidates interested",
            f"for candidates interested in {primary_keyword}"
        )

    return content


def main():
    """Update all articles to achieve 95+ SEO scores."""
    print("=" * 60)
    print("Updating Articles for Better SEO")
    print("=" * 60)

    client = BloggerClient()
    analyzer = SEOAnalyzer()

    for current_title, info in ARTICLES_TO_UPDATE.items():
        post_id = info["post_id"]
        keywords = info["keywords"]

        print(f"\n--- Processing: {current_title} ---")

        # Get current post from Blogger
        result = client.get_post(post_id)
        if not result.success:
            print(f"Could not fetch post: {result.error}")
            continue

        raw = result.raw_response
        existing_content = raw.get('content', '')

        # Optimize
        optimized_title = optimize_title(current_title, keywords)
        optimized_content = optimize_content(existing_content, optimized_title, keywords)

        # Check SEO
        seo_report = analyzer.analyze(optimized_title, optimized_content, target_keyword=keywords[0])
        print(f"SEO Score: {seo_report.overall_score}/100")
        print(f"  Title: {seo_report.title_score.value}")
        print(f"  Keyword: {seo_report.keyword_score.value}")
        print(f"  Readability: {seo_report.readability_score.value}")

        # Create optimized post
        post = BlogPost(
            title=optimized_title,
            content=optimized_content,
            labels=raw.get('labels', keywords),
        )

        # Update via publisher
        from core.publishing import Publisher
        publisher = Publisher()
        update_result = publisher.update_post(post_id, post)

        if update_result.success:
            print(f"✓ Updated: {update_result.url}")
        else:
            print(f"✗ Update failed: {update_result.error}")

    print("\n" + "=" * 60)
    print("All articles processed!")
    print("=" * 60)


if __name__ == "__main__":
    main()