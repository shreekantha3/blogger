#!/usr/bin/env python3
"""
Batch apply JobPosting schema to all recruitment articles.
"""

import re
from pathlib import Path


def apply_jobposting_schema(file_path: Path, org_name: str, last_date: str = None) -> bool:
    """Apply JobPosting schema to an article file."""

    if not file_path.exists():
        return False

    content = file_path.read_text()

    # Check if schema already exists
    if 'application/ld+json' in content:
        return False

    # Extract title
    title_match = re.search(r"<h1>(.*?)</h1>", content)
    if not title_match:
        return False

    title = title_match.group(1)

    # Determine file extension for output
    is_html = file_path.suffix == ".html"

    schema = f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "{title}",
  "datePosted": "2026-07-22",
  "hiringOrganization": {{
    "@type": "Organization",
    "name": "{org_name}"
  }},
  "jobLocation": {{
    "@type": "Place",
    "address": {{
      "@type": "PostalAddress",
      "addressLocality": "India"
    }}
  }},
  "description": "Government job recruitment with online application. Check eligibility and apply."
}}
</script>

'''

    updated = schema + content
    file_path.write_text(updated)
    return True


def main():
    """Process all recruitment articles."""
    articles_dir = Path("articles")

    # Map files to organizations
    recruitment_files = {
        "aiims-gorakhpur-recruitment-2026-junior-resident.md": "AIIMS Gorakhpur",
        "cotton-corporation-of-india-recruitment-2026.md": "Cotton Corporation of India",
        "ncbs-recruitment-2026-scientific-officer-c.html": "NCBS",
        "nhsrcl-recruitment-2026-technician-junior-engineer.md": "NHSRCL",
        "nimhans-recruitment-2026-counsellor-posts.html": "NIMHANS",
        "rites-recruitment-2026-am-sm-manager-posts.html": "RITES Limited",
        "tmb-recruitment-2026-senior-relationship-manager.md": "Tamilnad Mercantile Bank",
    }

    updated_count = 0

    for filename, org in recruitment_files.items():
        file_path = articles_dir / filename
        if file_path.exists() and apply_jobposting_schema(file_path, org):
            updated_count += 1
            print(f"✓ Added JobPosting schema to {filename}")
        elif file_path.exists():
            print(f"⊘ Schema already exists in {filename}")
        else:
            print(f"⊗ Not found: {filename}")

    print(f"\nTotal updated: {updated_count} articles")


if __name__ == "__main__":
    main()