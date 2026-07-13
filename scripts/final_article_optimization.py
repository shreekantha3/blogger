#!/usr/bin/env python3
"""
Final SEO optimization using template from successful articles.
Target: 95+ SEO score.
"""

import re
from pathlib import Path
from config import get_settings, setup_logging
from core.models import BlogPost
from core.publishing import Publisher
from seo import SEOAnalyzer

# Setup logging
settings = get_settings()
setup_logging(level=settings.log_level, log_format=settings.log_format)

ARTICLES_TO_PUBLISH = {
    "YASCCON Recruitment 2026": {
        "organization": "Yadagere Souharda Co-operative Society Limited (YASCCON)",
        "total_posts": "4 Posts",
        "posts": [
            {"name": "Chief Executive", "vacancies": "1", "qualification": "Graduation with MBA"},
            {"name": "Assistant", "vacancies": "1", "qualification": "Degree"},
            {"name": "Sub Staff", "vacancies": "2", "qualification": "10th Pass"}
        ],
        "apply_mode": "Offline",
        "start_date": "01-07-2026",
        "last_date": "15-Jul-2026",
        "application_fee": "No application fee is required",
        "selection_process": "Application screening followed by Personal Interview",
        "address": "Yadagere Souharda Co-operative Society Limited, Koppa, YASCCON Commercial Complex, T.M. Road, Koppa, Chikkamagaluru – 577126, Karnataka",
        "official_website": "souharda.coop",
        "keywords": ["YASCCON Recruitment 2026", "YASCCON Assistant Vacancy", "Souharda Society Jobs", "Karnataka Cooperative Jobs", "Offline Recruitment 2026"]
    },
    "KFWCCF Recruitment 2026": {
        "organization": "Karnataka Forest Wildlife Conservation Committee (KFWCCF)",
        "total_posts": "Multiple Posts",
        "posts": [
            {"name": "Public Relation Officer", "vacancies": "Multiple", "qualification": "Graduate degree"}
        ],
        "apply_mode": "Offline",
        "last_date": "25-02-2026",
        "application_fee": "No application fee",
        "salary": "₹1,50,000 monthly",
        "selection_process": "Work experience and educational review followed by Interview",
        "address": "Aranya Bhavan, 18th Cross, Malleshwaram, Bengaluru – 560 003",
        "official_website": "kfwccf.in",
        "contact": {"telephone": "080-23346551", "email": "kfwccf@aranya.gov.in"},
        "keywords": ["KFWCCF Recruitment 2026", "KFWCCF PRO Jobs", "Forest Jobs Karnataka", "Environmental Jobs", "Bengaluru Jobs 2026"]
    },
    "SAIL Recruitment 2026": {
        "organization": "Steel Authority of India Limited (SAIL)",
        "total_posts": "23 Young Professional Posts",
        "posts": [
            {"name": "Young Professional I", "vacancies": "23", "qualification": "B.Tech/B.E. or MBA"}
        ],
        "apply_mode": "Online",
        "last_date": "31 July 2026",
        "application_fee": "₹500 application fee",
        "salary": "₹70,000 per month",
        "selection_process": "Computer Based Test followed by Personal Interaction",
        "official_website": "sailcareers.com",
        "keywords": ["SAIL Recruitment 2026", "SAIL Young Professional", "Steel Jobs 2026", "Government Engineering Jobs", "SAIL Careers"]
    },
    "BGSSS Recruitment 2026": {
        "organization": "Baroda Global Shared Services (BGSSS)",
        "total_posts": "438 Posts",
        "posts": [
            {"name": "Aadhar Operator", "vacancies": "Multiple", "qualification": "12th Pass"},
            {"name": "Field Sales Officer", "vacancies": "240", "qualification": "Graduate"}
        ],
        "apply_mode": "Online",
        "last_date": "25 July 2026",
        "application_fee": "No fee required",
        "selection_process": "Written examination followed by Interview",
        "official_website": "bgss.in",
        "keywords": ["BGSSS Recruitment 2026", "Aadhar Operator Jobs", "Banking Jobs 2026", "Digital Banking Careers", "BGSSS Jobs"]
    },
    "WAMUL Recruitment 2026": {
        "organization": "West Assam Milk Union (WAMUL)",
        "total_posts": "Multiple Posts",
        "posts": [
            {"name": "Sr. Assistant", "vacancies": "Multiple", "qualification": "B.Com graduate"}
        ],
        "apply_mode": "Online",
        "last_date": "17 July 2026",
        "application_fee": "No application fee",
        "selection_process": "Merit list preparation followed by Interview",
        "official_website": "purabi.coop",
        "keywords": ["WAMUL Recruitment 2026", "Dairy Jobs Assam", "Cooperative Jobs", "WAMUL Vacancy", "Assam Jobs 2026"]
    }
}


def generate_optimized_html(topic: str, data: dict) -> str:
    """Generate HTML with proper formatting for 95+ SEO score."""
    primary = data["keywords"][0]

    # Post rows for table
    post_rows = ""
    for p in data["posts"]:
        post_rows += f'    <tr>\n      <td><strong>{p["name"]}</strong></td>\n      <td>{p["vacancies"]}</td>\n      <td>{p["qualification"]}</td>\n    </tr>\n'

    html = f'''<h1>{topic}: Complete Recruitment 2026 Details</h1>

<p><strong>Last Updated:</strong> July 2026 | <strong>Total Vacancies:</strong> {data["total_posts"]} | <strong>Apply Mode:</strong> {data["apply_mode"]}</p>

<h2>{topic} - Overview and Details</h2>

<p>{topic} announced by {data["organization"]}. Important jobs for 2026. Apply online.</p>

<table>
  <thead>
    <tr>
      <th>Post Name</th>
      <th>Vacancies</th>
      <th>Qualification</th>
    </tr>
  </thead>
  <tbody>
{post_rows}
  </tbody>
</table>

<h2>{data["organization"]} - Eligibility for {topic.split()[0]}</h2>

<h3>Education Required</h3>

<table>
  <thead>
    <tr>
      <th>Post</th>
      <th>Minimum Education</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Chief Executive</td>
      <td>Graduation with MBA preferred</td>
    </tr>
    <tr>
      <td>Assistant</td>
      <td>Degree from recognized university</td>
    </tr>
    <tr>
      <td>Sub Staff</td>
      <td>SSLC or 10th standard pass</td>
    </tr>
  </tbody>
</table>

<h3>Age Criteria</h3>

<p>Age as per official rules. Relaxation for reserved categories as per govt norms.</p>

<h2>{data["organization"]} Salary Details</h2>

<p>Pay as per matrix. Good salary with benefits. Check official note for range.</p>

<h2>{topic} - Selection Process</h2>

<p>Process: {data["selection_process"]}. Do well to get selected for {primary}.</p>

<h2>How to Apply - {topic.split()[0]} 2026</h2>

<h3>Application Steps</h3>

<ol>
  <li>Visit {data["official_website"]}</li>
  <li>Find careers section</li>
  <li>Download {topic.split()[0]} notification</li>
  <li>Check eligibility for {primary}</li>
  <li>Gather required documents</li>
  <li>Apply via {data["apply_mode"]} mode</li>
  <li>Submit by {data["last_date"]}</li>
</ol>

<h3>Important Dates for {primary}</h3>

<p>Last date: {data["last_date"]}</p>
<p>Fee: {data["application_fee"]}</p>

<h2>Documents for {topic.split()[0]} Apply</h2>

<ul>
  <li>Edu certificates - original and copies</li>
  <li>ID proof - Aadhaar/ PAN/ Passport</li>
  <li>DOB proof</li>
  <li>Caste certificate - if applicable</li>
  <li>Photo and signature</li>
</ul>

<h2>{topic} - FAQ</h2>

<h3>Q1. Total posts in {topic}?</h3>
<p>A. {data["total_posts"]} posts. Check {data["organization"]} website for {primary}.</p>

<h3>Q2. How to apply for {topic}?</h3>
<p>A. Apply {data["apply_mode"]}. Steps given above for {primary}.</p>

<h3>Q3. Last date for {topic}?</h3>
<p>A. Apply before {data["last_date"]}. Late forms not accepted.</p>

<h3>Q4. Selection for {topic}?</h3>
<p>A. Based on {data["selection_process"].lower()}. Prepare for {primary}.</p>

<h3>Q5. Fee for {topic}?</h5>
<p>A. {data["application_fee"]}. Check {data["organization"]} site for fee rules.</p>

<h2> Benefits for {data["organization"]} Jobs</h2>

<ul>
  <li>Job security and stability</li>
  <li>Good salary and perks</li>
  <li>Growth chances high</li>
  <li>Work life balance</li>
  <li>Pension after retirement</li>
</ul>

<h2>Important Links - {topic}</h2>

<table>
  <thead>
    <tr>
      <th>Link</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="https://{data['official_website']}">{data['official_website']}</a></td>
      <td>Official site for {primary}</td>
    </tr>
  </tbody>
</table>

<hr>

<p><strong>Focus Keyword:</strong> {topic}<br>
<strong>Keywords:</strong> {", ".join(data["keywords"])}<br>
<strong>Meta:</strong> {topic} {data["total_posts"]} vacancies. Apply before {data["last_date"]}. Check {data["official_website"]} for {primary}.</p>'''

    return html


def main():
    """Publish optimized articles to Blogger."""
    print("=" * 60)
    print("Publishing SEO Optimized Recruitment Articles")
    print("=" * 60)

    publisher = Publisher()
    analyzer = SEOAnalyzer()

    for topic, data in ARTICLES_TO_PUBLISH.items():
        print(f"\n--- {topic} ---")

        html = generate_optimized_html(topic, data)
        keywords = data["keywords"]

        # Check SEO
        report = analyzer.analyze(topic, html, target_keyword=keywords[0])
        print(f"SEO Score: {report.overall_score}/100")

        # Publish
        post = BlogPost(
            title=f"{topic}: Complete Recruitment 2026 Details",
            content=html,
            labels=keywords,
        )

        try:
            result = publisher.publish(post)
            if result.success:
                print(f"✓ Published: {result.url}")
            else:
                print(f"✗ Failed: {result.error}")
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()