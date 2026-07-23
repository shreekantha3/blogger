#!/usr/bin/env python3
"""
Generate JobPosting schema for published Blogger articles.

ARCHITECTURAL DECISION: Schema Deployment Helper
-------------------------------------------------
This script helps you apply schemas to already-published posts:
1. Generates JobPosting schema JSON-LD for each article
2. Shows you exactly what to copy/paste into Blogger HTML mode
3. Saves to a file you can reference during manual updates

Use this to apply the 10 schemas to your live Blogger posts.
"""

import json
from pathlib import Path

from ai.schema_howto import JobPostingSchemaGenerator


def generate_schemas_for_articles():
    """Generate and display schemas for all recruitment articles."""

    # Map articles to their data
    articles = {
        "Karnataka Excise Department Recruitment 2025": {
            "date_posted": "2026-07-22",
            "organization": "Karnataka Excise Department",
            "location": "Karnataka, India",
            "salary": "21,400 - 180,000",
            "description": "1,207 Excise Constable and Sub-Inspector posts. PUC/10th pass required."
        },
        "BOBCARD Recruitment 2026 Assistant Manager": {
            "date_posted": "2026-02-15",
            "valid_through": "2026-03-16T23:59",
            "organization": "BOB Financial Solutions Limited (BOBCARD)",
            "location": "Hyderabad, Mumbai, India",
            "description": "Assistant Manager - Collections. 2+ years experience required."
        },
        "IHMCL Recruitment 2026 Systems Engineer": {
            "date_posted": "2026-07-04",
            "valid_through": "2026-08-02T18:00",
            "organization": "Indian Highways Management Company Limited (IHMCL)",
            "location": "India (Transferable)",
            "description": "30 Systems Engineer posts. GATE required. Entry-level position."
        },
        "KSP Recruitment 2026 Civil Police Constable": {
            "date_posted": "2026-06-08",
            "valid_through": "2026-07-03T23:59",
            "organization": "Karnataka State Police (KSP)",
            "location": "Karnataka, India",
            "description": "3,991 Civil Police Constable positions. PUC/12th pass required."
        },
        "AIIMS Gorakhpur Recruitment 2026 Junior Resident": {
            "date_posted": "2026-07-22",
            "organization": "AIIMS Gorakhpur",
            "location": "Gorakhpur, India",
            "description": "Junior Resident positions for medical graduates."
        },
        "Cotton Corporation of India Recruitment 2026": {
            "date_posted": "2026-07-22",
            "organization": "Cotton Corporation of India",
            "location": "India",
            "description": "Government job recruitment for agriculture sector."
        },
        "NCBS Recruitment 2026 Scientific Officer C": {
            "date_posted": "2026-07-22",
            "organization": "NCBS",
            "location": "India",
            "description": "Scientific Officer C positions."
        },
        "NHSRCL Recruitment 2026 Technician Junior Engineer": {
            "date_posted": "2026-07-22",
            "organization": "NHSRCL",
            "location": "India",
            "description": "Technician and Junior Engineer positions."
        },
        "NIMHANS Recruitment 2026 Counsellor": {
            "date_posted": "2026-07-22",
            "organization": "NIMHANS",
            "location": "Bangalore, India",
            "description": "Counsellor positions for medical institution."
        },
        "RITES Recruitment 2026 AM SM Manager": {
            "date_posted": "2026-07-22",
            "organization": "RITES Limited",
            "location": "India",
            "description": "Assistant Manager and Senior Manager positions."
        },
        "TMB Recruitment 2026 Senior Relationship Manager": {
            "date_posted": "2026-07-22",
            "organization": "Tamilnad Mercantile Bank",
            "location": "Tamil Nadu, India",
            "description": "Senior Relationship Manager positions."
        }
    }

    generator = JobPostingSchemaGenerator()

    print("# JobPosting Schema for Published Blogger Articles")
    print()
    print("Copy each schema block and paste into Blogger post editor in HTML mode.")
    print("(Edit post → HTML view → paste after opening <body> tag)")
    print()

    for title, data in articles.items():
        print("=" * 60)
        print(f"## {title}")
        print("=" * 60)

        schema = generator.generate_jobposting(
            title=title,
            date_posted=data["date_posted"],
            valid_through=data.get("valid_through"),
            hiring_organization=data["organization"],
            job_location=data["location"],
            description=data["description"],
        )

        print("```json")
        print(json.dumps(schema, indent=2))
        print("```")
        print()


if __name__ == "__main__":
    generate_schemas_for_articles()