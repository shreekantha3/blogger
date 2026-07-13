#!/usr/bin/env python3
"""
Generate and publish 5 recruitment articles to Blogger with SEO optimization.
Uses RankMath SEO strategy with 95+ score target.
"""

import json
from pathlib import Path
from config import get_settings, setup_logging
from ai.generator import AIArticleGenerator
from ai.models import AIArticleRequest, MetaOptimizationRequest
from core.models import BlogPost
from core.publishing import Publisher
from seo import SEOAnalyzer
from seo.meta import MetaDescriptionGenerator

# Setup logging
settings = get_settings()
setup_logging(level=settings.log_level, log_format=settings.log_format, log_file_path=settings.log_file_path)

# Article topics and their recruitment data
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
            {"name": "Public Relation Officer (PRO)", "vacancies": "Multiple", "qualification": "Graduate degree in any discipline, preference for communication specialization"}
        ],
        "apply_mode": "Offline",
        "last_date": "25-02-2026",
        "application_fee": "No fee required",
        "salary": "₹1,50,000/- consolidated monthly",
        "selection_process": "Based on work experience, educational qualifications, and interview (total 100 marks)",
        "address": "Room No.: 103, Aranya Bhavan, 18th Cross, Malleshwaram, Bengaluru-560 003",
        "official_website": "http://kfwccf.in",
        "contact": {"telephone": "080-23346551", "email": "kfwccf@aranya.gov.in"},
        "keywords": ["KFWCCF Recruitment 2026", "KFWCCF PRO Recruitment", "Karnataka Forest Recruitment", "Public Relation Officer Jobs", "Environmental Jobs Karnataka", "KFWCCF Application", "Forest Jobs Bengaluru"]
    },
    "SAIL Recruitment 2026": {
        "organization": "Steel Authority of India Limited (SAIL)",
        "total_posts": "23 Young Professional I Posts",
        "posts": [
            {"name": "Young Professional I", "vacancies": "23", "qualification": "B.E/B.Tech in Mechanical, Electrical, Civil, CSE OR MBA, CA/CMA"}
        ],
        "apply_mode": "Online",
        "notification_release": "03 July 2026",
        "start_date": "10 July 2026",
        "last_date": "31 July 2026",
        "application_fee": "₹500/- for all candidates",
        "salary": "₹70,000/- per month",
        "selection_process": "Computer-Based Test (CBT) + Personal Interaction (80% CBT + 20% PI)",
        "official_website": "https://sailcareers.com/",
        "job_locations": ["Rourkela Steel Plant", "Ranchi", "Management Training Institute", "Safety Organization", "Digital Transformation Division"],
        "keywords": ["SAIL Recruitment 2026", "SAIL Young Professional Recruitment", "Steel Authority of India Jobs", "SAIL Online Application", "Young Professional I Vacancy", "SAIL Careers", "Government Jobs Steel Sector"]
    },
    "BGSSS Recruitment 2026": {
        "organization": "Baroda Global Shared Services Limited (BGSSS)",
        "total_posts": "438 Posts across Multiple Positions",
        "posts": [
            {"name": "Aadhar Operator", "vacancies": "Multiple", "qualification": "12th (Class 12)"},
            {"name": "Field Sales Officer (Loan)", "vacancies": "240", "qualification": "Various"},
            {"name": "Tele-Collection Agent", "vacancies": "100", "qualification": "Various"},
            {"name": "Executive (ATM/Reconciliation/Complaints/Debit Cards)", "vacancies": "40", "qualification": "Various"},
            {"name": "Executive/Sr. Executive – Digital Banking", "vacancies": "20", "qualification": "Various"},
            {"name": "Trade Finance Operations – Executive", "vacancies": "25", "qualification": "Various"}
        ],
        "apply_mode": "Online",
        "start_date": "01-07-2026",
        "last_date": "25-Jul-2026",
        "application_fee": "No fee required",
        "selection_process": "Written Test followed by Interview",
        "official_website": "https://www.bgss.in",
        "keywords": ["BGSSS Recruitment 2026", "BGSSS Jobs", "Baroda Global Shared Services Recruitment", "Aadhar Operator Jobs", "BGSSS Online Application", "Digital Banking Jobs", "Banking Sector Jobs"]
    },
    "WAMUL Recruitment 2026": {
        "organization": "West Assam Milk Producers Cooperative Union Limited (WAMUL) / Purabi Dairy",
        "total_posts": "Multiple Executive and Assistant Posts",
        "posts": [
            {"name": "Sr. Assistant/ Assistant", "vacancies": "Multiple", "qualification": "B.Com", "salary": "Rs.3.92,000 – 6.53,000/- per annum", "age_limit": "Max. 32 years"},
            {"name": "Deputy Assistant Manager", "vacancies": "Multiple", "qualification": "Post Gradification Degree/Diploma", "salary": "Rs.7.90,000 – 8.98,000/- per annum", "age_limit": "30-40 years"},
            {"name": "Executive/ Jr. Executive", "vacancies": "Multiple", "qualification": "B.Com"}
        ],
        "apply_mode": "Online",
        "start_date": "03-07-2026",
        "last_date": "17-Jul-2026 (for Sr. Assistant/Assistant), 28th July 2026 (Deputy Assistant Manager)",
        "application_fee": "No Application Fee required",
        "selection_process": "Merit List followed by Interview",
        "official_website": "https://purabi.coop",
        "job_locations": ["Nagaon", "Tezpur", "North Lakhimpur", "Silchar", "Guwahati", "Jorhat - Assam"],
        "keywords": ["WAMUL Recruitment 2026", "Purabi Dairy Jobs", "West Assam Milk Producers Recruitment", "WAMUL Assistant Jobs", "Dairy Sector Jobs Assam", "Cooperative Jobs", "WAMUL Careers"]
    }
}


def generate_article_html(topic: str, data: dict) -> str:
    """Generate SEO-optimized HTML article for recruitment topic with 95+ score target."""

    # Build post table rows
    post_rows = ""
    for post in data["posts"]:
        post_rows += f'    <tr>\n      <td><strong>{post["name"]}</strong></td>\n      <td>{post["vacancies"]} Posts</td>\n      <td>{post["qualification"]}</td>\n    </tr>\n'
    post_rows += f'    <tr>\n      <td><strong>Total Vacancies</strong></td>\n      <td><strong>{data["total_posts"]}</strong></td>\n      <td>-</td>\n    </tr>'

    # Build eligibility table
    eligibility_rows = ""
    for post in data["posts"]:
        eligibility_rows += f'    <tr>\n      <td><strong>{post["name"]}</strong></td>\n      <td>{post["qualification"]}</td>\n    </tr>\n'

    # Build salary table
    salary_rows = ""
    has_salary = any("salary" in post for post in data["posts"])
    if has_salary:
        for post in data["posts"]:
            if "salary" in post:
                salary_rows += f'    <tr>\n      <td><strong>{post["name"]}</strong></td>\n      <td>{post["salary"]}</td>\n    </tr>\n'
    else:
        if "salary" in data:
            salary_rows = f'    <tr>\n      <td><strong>All Posts</strong></td>\n      <td>{data["salary"]}</td>\n    </tr>'
        else:
            salary_rows = f'    <tr>\n      <td><strong>All Posts</strong></td>\n      <td>Competitive as per organization norms</td>\n    </tr>'

    # Build FAQ section
    selection_process_text = data.get("selection_process", "Merit-based selection")
    faq_html = f'''<h3>Q1. What is the total number of vacancies?</h3>
<p>A. There are <strong>{data['total_posts']}</strong> in {data['organization']} recruitment drive. Candidates meeting the eligibility criteria should apply before the last date.</p>

<h3>Q2. What is the application mode?</h3>
<p>A. Applications can be submitted <strong>{data['apply_mode']}</strong>. {'Follow the step-by-step guide provided in this article for complete application process.' if data['apply_mode'] == 'Online' else 'Download the application form from the official website and submit to the address provided.'}</p>

<h3>Q3. What is the last date to apply?</h3>
<p>A. The last date to apply is <strong>{data['last_date']}</strong>. Make sure to submit your application before this deadline to avoid disqualification.</p>

<h3>Q4. What is the selection process?</h3>
<p>A. Selection is based on {selection_process_text.lower()}. Prepare thoroughly for each stage of the selection process to maximize your chances.</p>

<h3>Q5. Is there any application fee?</h3>
<p>A. {data['application_fee']}. Check the official notification for any fee exemptions for reserved category candidates.</p>'''

    # Build important links
    links_html = f'''    <tr>
      <td><a href="{data["official_website"]}" target="_blank" rel="noopener noreferrer">Official Website</a></td>
      <td>Check latest notifications and apply online</td>
    </tr>
'''
    if "contact" in data:
        links_html += f'''    <tr>
      <td>Contact Email</td>
      <td>{data["contact"]["email"]}</td>
    </tr>
    <tr>
      <td>Contact Phone</td>
      <td>{data["contact"]["telephone"]}</td>
    </tr>
'''

    # Generate SEO-optimized meta description (120-155 chars)
    meta_desc = f"Apply for {topic} {data['total_posts']}. Check eligibility, selection process, application mode ({data['apply_mode']}), and important dates. {data['organization']} recruitment notification details."
    meta_desc = meta_desc[:155] if len(meta_desc) > 155 else meta_desc

    html = f'''<h1>{topic}: Complete Recruitment Guide 2026 - Apply Before Last Date</h1>

<p><strong>Last Updated:</strong> July 2026 | <strong>Total Posts:</strong> {data["total_posts"]} | <strong>Application Mode:</strong> {data["apply_mode"]} | <strong>Organization:</strong> {data["organization"]}</p>

<h2>{topic} - Introduction and Overview</h2>

<p>{data["organization"]} has announced recruitment for {data["total_posts"]} across various positions for 2026. This is an excellent opportunity for candidates seeking employment in the cooperative sector with competitive salary packages and job security. The recruitment drive aims to fill positions across multiple departments.</p>

<h2>{topic} - Complete Vacancy Details</h2>

<table>
  <thead>
    <tr>
      <th>Post Name</th>
      <th>Number of Vacancies</th>
      <th>Qualification Required</th>
    </tr>
  </thead>
  <tbody>
{post_rows}
  </tbody>
</table>

<p><strong>Official Website:</strong> <a href="{data["official_website"]}" target="_blank" rel="noopener noreferrer">{data["official_website"]}</a></p>

<h2>{data["organization"]} Recruitment - Eligibility Criteria</h2>

<h3>Educational Qualification Requirements</h3>

<table>
  <thead>
    <tr>
      <th>Post</th>
      <th>Minimum Qualification</th>
    </tr>
  </thead>
  <tbody>
{eligibility_rows}
  </tbody>
</table>

<p>Candidates must possess the minimum educational qualification as specified above. All qualifications must be from recognized boards and universities.</p>

<h3>Age Limit Details</h3>

<table>
  <thead>
    <tr>
      <th>Category</th>
      <th>Age Limit</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>All Posts</strong></td>
      <td>{data.get("age_limit", "As per government notification")}</td>
    </tr>
  </tbody>
</table>

<p>Age relaxation is applicable as per government rules for SC, ST, OBC, and other reserved categories.</p>

<h2>{data["organization"]} Salary and Benefits</h2>

<table>
  <thead>
    <tr>
      <th>Post</th>
      <th>Salary/Pay Scale</th>
    </tr>
  </thead>
  <tbody>
{salary_rows}
  </tbody>
</table>

<h3>Additional Benefits and Perks</h3>
<ul>
  <li>Govt. Job Security and stability with regular salary increments</li>
  <li>Medical benefits for self and family members</li>
  <li>Pension scheme after retirement with government backing</li>
  <li>Dearness allowance and House Rent Allowance (HRA)</li>
  <li>Casual leave, medical leave, and earned leave benefits</li>
  <li>Provident Fund and other retirement benefits</li>
</ul>

<h2>Selection Process - Detailed Analysis</h2>

<p>The selection process for {topic} involves: <strong>{selection_process_text}</strong>. Understanding each stage helps candidates prepare better for the recruitment journey.</p>

<h3>Application Process Steps</h3>
<ol>
  <li><strong>Visit Official Website:</strong> {data["official_website"]} - Access the official careers portal</li>
  <li><strong>Check Careers Section:</strong> Look for latest recruitment notification and download PDF</li>
  <li><strong>Read Official Notification:</strong> Review complete advertisement for all requirements</li>
  <li><strong>Verify Eligibility:</strong> Check age, educational, and experience requirements thoroughly</li>
  <li><strong>Prepare Documents:</strong> Scan certificates in prescribed format (PDF/JPG)</li>
  <li><strong>Submit Application:</strong> Follow the {data["apply_mode"]} application process as per guidelines</li>
  <li><strong>Print Acknowledgment:</strong> Save confirmation page for future reference</li>
</ol>

<h2>How to Apply - Complete Step-by-Step Process</h2>

<h3>Important Dates and Deadlines</h3>

<p><strong>Application Mode:</strong> {data["apply_mode"]}</p>
<p><strong>Application Start Date:</strong> {data.get("start_date", "To be announced soon")}</p>
<p><strong>Last Date to Apply:</strong> {data["last_date"]}</p>
<p><strong>Application Fee:</strong> {data["application_fee"]}</p>

<h3>Submission Address for Offline Applications</h3>
<p>{data.get("address", "Refer to official notification for address details")}</p>

<h2>Documents Required for Application</h2>

<h3>Essential Documents Checklist</h3>
<p>Candidates must prepare the following documents in original and photocopy format:</p>

<ul>
  <li>Educational Certificates - Original and self-attested photocopies</li>
  <li>Identity Proof (Aadhaar Card, PAN Card, Passport, Driving License)</li>
  <li>Date of Birth Certificate (SSLC or Birth Certificate)</li>
  <li>Category Certificate (SC/ST/OBC/EWS) - if applicable for reserved category</li>
  <li>Experience Certificates - if applicable for the applied position</li>
  <li>Passport Size Photograph (white background, recent)</li>
  <li>Signature on white paper matching identity proof</li>
  <li>Domicile Certificate - if required by the organization</li>
</ul>

<h2>{data["organization"]} Recruitment - Frequently Asked Questions</h2>

{faq_html}

<h2>Why Apply for {data["organization"]} Jobs?</h2>

<p>Joining {data["organization"]} offers several advantages for career-oriented candidates:</p>

<ul>
  <li><strong>Govt. Job Security:</strong> Permanent employment with long-term stability and regular increments</li>
  <li><strong>Career Growth:</strong> Clear promotion pathway to higher ranks within the organization</li>
  <li><strong>Work-Life Balance:</strong> Regular working hours and well-defined duties ensure work-life harmony</li>
  <li><strong>Benefits Package:</strong> Medical, pension, and other allowances including DA and HRA</li>
  <li><strong>Pride of Service:</strong> Contribution to society and nation through meaningful work</li>
  <li><strong>Professional Development:</strong> Training and skill development opportunities</li>
</ul>

<h2>Important Links and Resources</h2>

<table>
  <thead>
    <tr>
      <th>Link</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
{links_html}
  </tbody>
</table>

<hr>

<p><strong>Focus Keyword:</strong> {topic}<br>
<strong>Keywords:</strong> {", ".join(data["keywords"])}<br>
<strong>Meta Description:</strong> {meta_desc}</p>'''

    return html


def optimize_seo(title: str, content: str, keywords: list[str]) -> tuple:
    """Optimize article to achieve 95+ SEO score."""
    from seo.meta import MetaDescriptionGenerator

    # Optimize title length (50-70 chars)
    if len(title) < 50:
        title = f"{title}: Complete Recruitment Guide 2026"
    elif len(title) > 70:
        title = title[:67] + "..."

    # Ensure proper content structure for SEO
    import re

    # Check for heading structure
    h1_count = len(re.findall(r'<h1>', content, re.IGNORECASE))
    h2_count = len(re.findall(r'<h2>', content, re.IGNORECASE))

    # Add more content if needed for better SEO
    if h2_count < 5:
        # Add additional sections for better SEO
        additional_sections = '''
<h2>Important Notifications and Updates</h2>

<p>Stay updated with the latest notifications from {data["organization"]}. All important announcements regarding {topic} will be published on the official website. Candidates are advised to bookmark the website and check regularly for updates.</p>

<h2>Preparation Tips for Selection Process</h2>

<p>For better preparation, candidates should: Review previous year question papers, Understand the selection criteria, Prepare all required documents in advance, and Follow the application process carefully to avoid last-minute issues.</p>
'''
        # Insert before the FAQ section
        content = content.replace(
            f'<h2>{data["organization"]} Recruitment - Frequently Asked Questions</h2>',
            additional_sections + f'<h2>{data["organization"]} Recruitment - Frequently Asked Questions</h2>'
        )

    # Generate meta description
    meta_generator = MetaDescriptionGenerator()
    meta_desc = meta_generator.generate(content, title=title)

    # Optimize meta description length
    if len(meta_desc) < 120:
        meta_desc = f"{meta_desc[:110]} - Complete details inside."
    elif len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."

    return title, content, meta_desc


def check_seo(title: str, content: str, keywords: list[str]) -> dict:
    """Check SEO quality of the article."""
    analyzer = SEOAnalyzer()
    report = analyzer.analyze(title, content, target_keyword=keywords[0] if keywords else None)

    return {
        "overall_score": report.overall_score,
        "title_score": report.title_score.value,
        "meta_score": report.meta_score.value,
        "heading_score": report.heading_score.value,
        "keyword_score": report.keyword_score.value,
        "readability_score": report.readability_score.value,
        "issues": report.all_issues[:5],
        "suggestions": report.all_suggestions[:5]
    }


def main():
    """Generate and publish all 5 recruitment articles."""
    print("=" * 60)
    print("Generating SEO-Optimized Recruitment Articles (RankMath Strategy)")
    print("=" * 60)

    publisher = Publisher()

    for topic, data in ARTICLES_DATA.items():
        print(f"\n--- Processing: {topic} ---")

        # Generate HTML content
        html_content = generate_article_html(topic, data)
        keywords = data["keywords"]

        # Optimize for SEO (95+ score target)
        optimized_title, optimized_content, meta_desc = optimize_seo(topic, html_content, keywords)

        # Check SEO score
        seo_report = check_seo(optimized_title, optimized_content, keywords)
        print(f"SEO Score: {seo_report['overall_score']}/100")
        print(f"  Title: {seo_report['title_score']}/100")
        print(f"  Meta: {seo_report['meta_score']}/100")
        print(f"  Headings: {seo_report['heading_score']}/100")
        print(f"  Keywords: {seo_report['keyword_score']}/100")

        # Create blog post with optimized content
        post = BlogPost(
            title=optimized_title,
            content=optimized_content,
            labels=keywords,
        )

        # Publish to Blogger
        try:
            result = publisher.publish(post)
            if result.success:
                print(f"✓ Published: {result.url}")
                print(f"  Post ID: {result.post_id}")

                # Save article locally
                article_path = Path(f"articles/{topic.lower().replace(' ', '-')}.html")
                article_path.parent.mkdir(parents=True, exist_ok=True)
                article_path.write_text(optimized_content)
                print(f"  Saved locally: {article_path}")
            else:
                print(f"✗ Failed: {result.error}")

                # Save locally even if publish fails
                article_path = Path(f"articles/{topic.lower().replace(' ', '-')}.html")
                article_path.parent.mkdir(parents=True, exist_ok=True)
                article_path.write_text(optimized_content)
                print(f"  Saved locally (publish failed): {article_path}")
        except Exception as e:
            print(f"✗ Error publishing: {e}")

            # Save locally
            article_path = Path(f"articles/{topic.lower().replace(' ', '-')}.html")
            article_path.parent.mkdir(parents=True, exist_ok=True)
            article_path.write_text(optimized_content)
            print(f"  Saved locally: {article_path}")

    print("\n" + "=" * 60)
    print("All articles processed!")
    print("=" * 60)


if __name__ == "__main__":
    main()