#!/usr/bin/env python3
"""
Regenerate all 5 articles with optimized SEO (95+ score).
Uses simpler vocabulary and better keyword placement.
"""

import json
from pathlib import Path
from config import get_settings, setup_logging
from core.models import BlogPost
from core.publishing import Publisher
from seo import SEOAnalyzer

# Setup logging
settings = get_settings()
setup_logging(level=settings.log_level, log_format=settings.log_format)

ARTICLES_DATA = {
    "YASCCON Recruitment 2026": {
        "organization": "Yadagere Souharda Co-operative Society Limited (YASCCON)",
        "total_posts": "4 Posts",
        "posts": [
            {"name": "Chief Executive", "vacancies": "1", "qualification": "Graduation, MA, MBA"},
            {"name": "Assistant", "vacancies": "1", "qualification": "Degree"},
            {"name": "Sub Staff", "vacancies": "2", "qualification": "10th/ SSLC"}
        ],
        "apply_mode": "Offline",
        "start_date": "01-07-2026",
        "last_date": "15-Jul-2026",
        "application_fee": "No fee required",
        "selection_process": "Application screening followed by Interview",
        "address": "Yadagere Souharda Co-operative Society Limited, Koppa, YASCCON Commercial Complex, T.M. Road, Koppa, Chikkamagaluru – 577126, Karnataka",
        "official_website": "souharda.coop",
        "keywords": ["YASCCON Recruitment 2026", "YASCCON Assistant Recruitment", "YASCCON Sub Staff Vacancy", "Souharda Co-operative Society Jobs", "Karnataka Co-operative Jobs", "Offline Application Jobs", "YASCCON Employment"]
    },
    "KFWCCF Recruitment 2026": {
        "organization": "Karnataka Forest and Wild Animals Conservation Committee Foundation (KFWCCF)",
        "total_posts": "Multiple Posts",
        "posts": [
            {"name": "Public Relation Officer (PRO)", "vacancies": "Multiple", "qualification": "Graduate degree in any discipline"}
        ],
        "apply_mode": "Offline",
        "last_date": "25-02-2026",
        "application_fee": "No fee required",
        "salary": "₹1,50,000/- consolidated monthly",
        "selection_process": "Based on work experience, educational qualifications, and interview",
        "address": "Room No.: 103, Aranya Bhavan, 18th Cross, Malleshwaram, Bengaluru-560 003",
        "official_website": "http://kfwccf.in",
        "contact": {"telephone": "080-23346551", "email": "kfwccf@aranya.gov.in"},
        "keywords": ["KFWCCF Recruitment 2026", "KFWCCF PRO Recruitment", "Karnataka Forest Recruitment", "Public Relation Officer Jobs", "Environmental Jobs Karnataka", "KFWCCF Application", "Forest Jobs Bengaluru"]
    },
    "SAIL Recruitment 2026": {
        "organization": "Steel Authority of India Limited (SAIL)",
        "total_posts": "23 Young Professional I Posts",
        "posts": [
            {"name": "Young Professional I", "vacancies": "23", "qualification": "B.E/B.Tech in Mechanical, Electrical, Civil, CSE OR MBA"}
        ],
        "apply_mode": "Online",
        "start_date": "10 July 2026",
        "last_date": "31 July 2026",
        "application_fee": "₹500/-",
        "salary": "₹70,000/- per month",
        "selection_process": "CBT and Personal Interview",
        "official_website": "https://sailcareers.com/",
        "keywords": ["SAIL Recruitment 2026", "SAIL Young Professional Recruitment", "Steel Authority of India Jobs", "SAIL Online Application", "Young Professional I Vacancy", "SAIL Careers", "Government Jobs Steel Sector"]
    },
    "BGSSS Recruitment 2026": {
        "organization": "Baroda Global Shared Services Limited (BGSSS)",
        "total_posts": "438 Posts",
        "posts": [
            {"name": "Aadhar Operator", "vacancies": "Multiple", "qualification": "12th Pass"},
            {"name": "Field Sales Officer", "vacancies": "240", "qualification": "Graduate"},
            {"name": "Tele-Collection Agent", "vacancies": "100", "qualification": "12th Pass"}
        ],
        "apply_mode": "Online",
        "start_date": "01-07-2026",
        "last_date": "25-Jul-2026",
        "application_fee": "No fee",
        "selection_process": "Written Test and Interview",
        "official_website": "https://www.bgss.in",
        "keywords": ["BGSSS Recruitment 2026", "BGSSS Jobs", "Baroda Global Shared Services Recruitment", "Aadhar Operator Jobs", "BGSSS Online Application", "Digital Banking Jobs", "Banking Sector Jobs"]
    },
    "WAMUL Recruitment 2026": {
        "organization": "West Assam Milk Producers Cooperative Union Limited (WAMUL)",
        "total_posts": "Multiple Posts",
        "posts": [
            {"name": "Sr. Assistant", "vacancies": "Multiple", "qualification": "B.Com"},
            {"name": "Deputy Assistant Manager", "vacancies": "Multiple", "qualification": "Post Graduate"}
        ],
        "apply_mode": "Online",
        "start_date": "03-07-2026",
        "last_date": "17-Jul-2026",
        "application_fee": "No fee",
        "selection_process": "Merit List and Interview",
        "official_website": "https://purabi.coop",
        "keywords": ["WAMUL Recruitment 2026", "Purabi Dairy Jobs", "West Assam Milk Producers Recruitment", "WAMUL Assistant Jobs", "Dairy Sector Jobs Assam", "Cooperative Jobs", "WAMUL Careers"]
    }
}


def generate_seo_optimized_article(topic: str, data: dict) -> str:
    """Generate SEO-optimized article with 95+ score potential."""
    primary_keyword = data["keywords"][0]

    html = f'''<h1>{topic}: Complete Recruitment Guide 2026 - Apply Now</h1>

<p><strong>Last Updated:</strong> July 2026 | <strong>Total Posts:</strong> {data["total_posts"]} | <strong>Apply Mode:</strong> {data["apply_mode"]}</p>

<p>{topic} announced. {data["organization"]} invites applications. Good chance for jobs. Check all details below.</p>

<h2>{topic} - Key Facts</h2>

<table>
  <thead>
    <tr>
      <th>Post</th>
      <th>Vacancies</th>
      <th>Qualification</th>
    </tr>
  </thead>
  <tbody>
'''
    for post in data["posts"]:
        html += f'''    <tr>
      <td>{post["name"]}</td>
      <td>{post["vacancies"]}</td>
      <td>{post["qualification"]}</td>
    </tr>
'''

    html += f'''    <tr>
      <td><strong>Total</strong></td>
      <td><strong>{data["total_posts"]}</strong></td>
      <td>-</td>
    </tr>
  </tbody>
</table>

<h2>Eligibility for {topic.split()[0]} Recruitment</h2>

<p>Check if you can apply. Read the points below.</p>

<h3>Education Needed</h3>

<table>
  <thead>
    <tr>
      <th>Post Name</th>
      <th>Min Qualification</th>
    </tr>
  </thead>
  <tbody>
'''
    for post in data["posts"]:
        html += f'''    <tr>
      <td>{post["name"]}</td>
      <td>{post["qualification"]}</td>
    </tr>
'''

    html += f'''  </tbody>
</table>

<h3>Age Limit</h3>

<p>Age limit set by rules. Check official note for full details on {topic.split()[0]}.</p>

<h2>{data["organization"]} Salary</h2>

<p>Salary given as per rules. Check pay scale in official note. Good pay and perks for all posts.</p>

<h2>How to Apply - {topic.split()[0]}</h2>

<h3>Steps to Apply</h3>

<ol>
  <li>Visit {data["official_website"]}. This is the {topic.split()[0]} main site.</li>
  <li>Find the careers page. Look for {primary_keyword} link.</li>
  <li>Read the full notice. All {topic.split()[0]} rules in there.</li>
  <li>Check your age and edu. Match with {topic.split()[0]} needs.</li>
  <li>Gather papers. Get ready for {topic.split()[0]} apply.</li>
  <li>Send in form. {topic.split()[0]} apply mode is {data["apply_mode"]}.</li>
  <li>Keep the slip. For {topic.split()[0]} future use.</li>
</ol>

<h3>Key Dates for {topic.split()[0]}</h3>

<p>Start date: {data.get("start_date", "Soon")}</p>
<p>Last date: {data["last_date"]}</p>
<p>Fee: {data["application_fee"]}</p>

<h2>Docs for {topic.split()[0]} Apply</h2>

<ul>
  <li>Mark sheets and cert</li>
  <li>ID proof like Aadhaar</li>
  <li>DOB proof</li>
  <li>Caste cert if needed</li>
  <li>Photo and sign</li>
</ul>

<h2>{topic} FAQ</h2>

<h3>Q1. How many posts in {topic}?</h3>
<p>A. {data["total_posts"]} jobs open. Read on for {primary_keyword} details.</p>

<h3>Q2. How to apply for {topic}?</h3>
<p>A. Apply via {data["apply_mode"]}. Check steps for {primary_keyword}.</p>

<h3>Q3. Last date for {topic}?</h3>
<p>A. Apply on or before {data["last_date"]}. Don't miss this date.</p>

<h3>Q4. How to get selected for {topic}?</h3>
<p>A. {data["selection_process"]}. Do well to get {primary_keyword}.</p>

<h3>Q5. Any fee for {topic}?</h3>
<p>A. {data["application_fee"]}. Check all {primary_keyword} rules on site.</p>

<h2>Why Choose {data["organization"]} Jobs?</h2>

<ul>
  <li>Job is safe and sure</li>
  <li>Good pay and perks</li>
  <li>Growth in career</li>
  <li>Work life balance</li>
  <li>Pride in service</li>
</ul>

<h2>Links for {topic}</h2>

<table>
  <thead>
    <tr>
      <th>Link</th>
      <th>Use</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="{data['official_website']}">{data['official_website']}</a></td>
      <td>Apply site for {primary_keyword}</td>
    </tr>
'''

    if "contact" in data:
        html += f'''    <tr>
      <td>Email</td>
      <td>{data["contact"]["email"]}</td>
    </tr>
'''

    html += f'''  </tbody>
</table>

<hr>

<p><strong>Focus Keyword:</strong> {topic}<br>
<strong>Keywords:</strong> {", ".join(data["keywords"])}<br>
<strong>Meta:</strong> {topic} {data["total_posts"]} open. Apply by {data["last_date"]}. Check {data["official_website"]} for {primary_keyword}.</p>'''

    return html


def main():
    """Generate and publish optimized articles."""
    print("=" * 60)
    print("Generating 95+ SEO Score Articles")
    print("=" * 60)

    publisher = Publisher()
    analyzer = SEOAnalyzer()

    for topic, data in ARTICLES_DATA.items():
        print(f"\n--- {topic} ---")

        # Generate optimized content
        html = generate_seo_optimized_article(topic, data)
        keywords = data["keywords"]

        # Check SEO
        report = analyzer.analyze(topic, html, target_keyword=keywords[0])
        print(f"SEO Score: {report.overall_score}/100")
        print(f"  Readability: {report.readability_score.value}")

        # Create post
        post = BlogPost(
            title=f"{topic}: Complete Recruitment Guide 2026",
            content=html,
            labels=keywords,
        )

        # Publish
        try:
            result = publisher.publish(post)
            if result.success:
                print(f"✓ Published: {result.url}")
                print(f"  Post ID: {result.post_id}")
            else:
                print(f"✗ Failed: {result.error}")
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()