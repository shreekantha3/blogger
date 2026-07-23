#!/usr/bin/env python3
"""
Apply JobPosting schema to recruitment articles.

ARCHITECTURAL DECISION: Schema Application Script
-------------------------------------------------
This script:
1. Parses recruitment articles for key data
2. Generates JobPosting schema JSON-LD
3. Injects schema into article HTML
4. Saves updated articles

Addresses Honest Code Review: "JobPosting schema - HIGH PRIORITY for recruitment"
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from ai.schema_howto import JobPostingSchemaGenerator


def extract_recruitment_data(content: str, title: str) -> dict:
    """Extract recruitment details from article content."""
    data = {
        "title": title,
        "date_posted": datetime.now().strftime("%Y-%m-%d"),
        "valid_through": None,
        "hiring_organization": "Unknown",
        "job_location": "India",
        "salary_currency": "INR",
        "salary_value": "N/A",
    }

    # Extract organization
    org_match = re.search(r"(?i)([\w\s]+Department|[\w\s]+Board|[\w\s]+Commission)", title)
    if org_match:
        data["hiring_organization"] = org_match.group(1).strip()

    # Extract last date if present
    last_date_match = re.search(r"(?:Last Date|Application End).*?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", content, re.IGNORECASE)
    if last_date_match:
        date_str = last_date_match.group(1)
        # Normalize date format
        date_str = date_str.replace("/", "-").replace("-", "-2025-", 1) if "-" in date_str else date_str
        data["valid_through"] = date_str

    # Extract total posts
    posts_match = re.search(r"(\d+[,\d]*)\s*(?:Posts|Vacancies|Positions)", content)
    if posts_match:
        data["description"] = f"Total posts available: {posts_match.group(1)}"

    # Extract salary range
    salary_match = re.search(r"(?:₹|Rs\.?)\s*([\d,]+(?:\s*[-–]\s*[\d,]+)?)", content)
    if salary_match:
        data["salary_value"] = salary_match.group(1)

    return data


def inject_schema(content: str, schema: dict) -> str:
    """Inject JSON-LD schema into HTML content."""
    schema_script = f'\n<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>\n'

    # Insert after opening <body> or <article> tag, or at start
    body_match = re.search(r"<body[^>]*>", content)
    if body_match:
        insert_pos = body_match.end()
        return content[:insert_pos] + schema_script + content[insert_pos:]
    else:
        return schema_script + content


def process_articles(directory: str = "articles", output_dir: str = None):
    """Process all recruitment article files."""
    dir_path = Path(directory)
    out_path = Path(output_dir) if output_dir else dir_path

    generator = JobPostingSchemaGenerator()

    # Find recruitment article files
    recruitment_files = list(dir_path.glob("*recruitment*.md")) + list(dir_path.glob("*recruitment*.html"))

    print(f"Found {len(recruitment_files)} recruitment articles")

    for file_path in recruitment_files:
        print(f"\nProcessing: {file_path.name}")

        content = file_path.read_text()

        # Extract title
        title_match = re.search(r"<h1>(.*?)</h1>", content)
        if not title_match:
            print(f"  ⚠ No H1 title found")
            continue

        title = title_match.group(1)

        # Extract recruitment data
        data = extract_recruitment_data(content, title)

        # Generate schema
        schema = generator.generate_jobposting(
            title=data["title"],
            date_posted=data["date_posted"],
            valid_through=data.get("valid_through"),
            hiring_organization=data["hiring_organization"],
            job_location=data["job_location"],
            salary_currency=data["salary_currency"],
            salary_value=data["salary_value"],
            description=data.get("description"),
        )

        # Check if schema already exists
        if 'application/ld+json' in content:
            print(f"  ✓ Schema already exists")
            continue

        # Inject schema
        updated = inject_schema(content, schema)

        # Save to output
        output_file = out_path / file_path.name
        output_file.write_text(updated)

        print(f"  ✓ Added JobPosting schema")
        print(f"    Organization: {data['hiring_organization']}")
        print(f"    Salary: {data['salary_value']}")


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "articles"
    output = sys.argv[2] if len(sys.argv) > 2 else None
    process_articles(directory, output)