"""
HowTo and JobPosting schema generators.

ARCHITECTURAL DECISION: Extended Schema Types
----------------------------------------------
Based on the Honest Code Review recommendation to expand schema types.

Current schemas: Article, FAQ, BreadcrumbList
Added schemas: HowTo, HowToStep, HowToSection, JobPosting, VideoObject

These drive rich snippets and improve CTR.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class HowToSchemaGenerator:
    """
    Generate HowTo schema for tutorial/rich snippet content.

    Usage:
        generator = HowToSchemaGenerator()
        schema = generator.generate_howto(
            title="How to Apply for KSP Recruitment",
            steps=[
                {"text": "Visit the official website", "url": "/step1"},
                {"text": "Fill the application form", "url": "/step2"},
            ]
        )
    """

    def generate_howto(
        self,
        title: str,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None,
        total_time: Optional[str] = None,
        estimated_cost: Optional[Dict[str, Any]] = None,
        tool: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate HowTo JSON-LD schema.

        Args:
            title: How-to title
            steps: List of step dicts with 'text', 'url' (optional), 'image' (optional)
            description: Brief description
            total_time: ISO 8601 duration (e.g., "PT1H30M")
            estimated_cost: Dict with '@type', 'currency', 'value'
            tool: Tool required for the how-to

        Returns:
            HowTo schema dictionary
        """
        howto_steps = []
        for i, step in enumerate(steps, 1):
            howto_step = {
                "@type": "HowToStep",
                "text": step.get("text", ""),
                "position": i,
                "name": f"Step {i}",
            }

            if "url" in step:
                howto_step["url"] = step["url"]
            if "image" in step:
                howto_step["image"] = step["image"]

            howto_steps.append(howto_step)

        schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": title,
            "step": howto_steps,
        }

        if description:
            schema["description"] = description

        if total_time:
            schema["totalTime"] = total_time

        if estimated_cost:
            schema["estimatedCost"] = estimated_cost

        if tool:
            schema["tool"] = tool

        return schema

    def generate_howto_from_html(
        self,
        title: str,
        html_content: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract HowTo steps from HTML content with numbered sections.

        Parses H2/H3 with numbers to create steps.
        """
        import re

        steps = []
        # Match H2/H3 sections
        pattern = r"<h[23][^>]*>([^<]*(?:\d+|\w+)[^<]*)</h[23]>"
        matches = re.findall(pattern, html_content)

        for match in matches[:15]:  # Max 15 steps
            steps.append({
                "text": re.sub(r"<[^>]+>", "", match).strip(),
                "name": f"Step {len(steps) + 1}",
            })

        return self.generate_howto(
            title=title,
            steps=steps,
            description=description,
        )


class JobPostingSchemaGenerator:
    """
    Generate JobPosting schema for recruitment articles.

    HIGH PRIORITY: This directly applies to existing recruitment content.

    Usage:
        generator = JobPostingSchemaGenerator()
        schema = generator.generate_jobposting(
            title="KSP Recruitment 2026 - Constable",
            date_posted="2026-07-15",
            valid_through="2026-08-15",
            hiring_organization="Karnataka State Police",
            job_location="Karnataka, India",
            salary_currency="INR",
            salary_value="45000",
        )
    """

    def generate_jobposting(
        self,
        title: str,
        date_posted: str,
        valid_through: Optional[str] = None,
        hiring_organization: Optional[str] = None,
        job_location: Optional[str] = None,
        salary_currency: Optional[str] = None,
        salary_value: Optional[str] = None,
        description: Optional[str] = None,
        application_contact: Optional[str] = None,
        employment_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate JobPosting JSON-LD schema.

        Args:
            title: Job title
            date_posted: ISO date string (YYYY-MM-DD)
            valid_through: Application deadline (YYYY-MM-DD)
            hiring_organization: Organization name
            job_location: Job location
            salary_currency: Currency code (INR, USD, etc.)
            salary_value: Salary value or range
            description: Job description
            application_contact: Contact email/phone
            employment_type: Type (FULL_TIME, PART_TIME, etc.)

        Returns:
            JobPosting schema dictionary
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": title,
            "datePosted": date_posted,
        }

        # Add validity dates
        if valid_through:
            # Handle both full datetime and date-only formats
            if "T" in valid_through:
                schema["validThrough"] = valid_through
            else:
                schema["validThrough"] = f"{valid_through}T23:59"

        # Add organization
        if hiring_organization:
            schema["hiringOrganization"] = {
                "@type": "Organization",
                "name": hiring_organization,
            }

        # Add location
        if job_location:
            schema["jobLocation"] = {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": job_location,
                }
            }

        # Add salary
        if salary_currency and salary_value:
            schema["baseSalary"] = {
                "@type": "MonetaryAmount",
                "currency": salary_currency,
                "value": salary_value,
            }

        # Add description (truncate to reasonable length)
        if description:
            schema["description"] = description[:2000]

        # Add employment type
        if employment_type:
            schema["employmentType"] = employment_type

        # Add application contact
        if application_contact:
            schema["applicationContact"] = {
                "@type": "ContactPoint",
                "email": application_contact,
            }

        return schema

    def generate_from_recruitment_data(
        self,
        title: str,
        notification_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate JobPosting schema from recruitment notification data.

        Args:
            title: Job title
            notification_data: Dict with recruitment details

        Returns:
            JobPosting schema
        """
        return self.generate_jobposting(
            title=title,
            date_posted=notification_data.get("notification_date", ""),
            valid_through=notification_data.get("last_date", ""),
            hiring_organization=notification_data.get("organization", ""),
            job_location=notification_data.get("location", ""),
            salary_currency=notification_data.get("salary_currency", "INR"),
            salary_value=notification_data.get("salary", ""),
            description=notification_data.get("description", ""),
            employment_type=notification_data.get("employment_type", "FULL_TIME"),
        )


class VideoObjectSchemaGenerator:
    """
    Generate VideoObject schema for video content.

    Usage:
        generator = VideoObjectSchemaGenerator()
        schema = generator.generate_video(
            name="Python Tutorial",
            description="Learn Python basics",
            thumbnail_url="https://example.com/thumb.jpg",
            upload_date="2026-07-15",
            duration="PT15M",
            content_url="https://youtube.com/watch?v=...",
        )
    """

    def generate_video(
        self,
        name: str,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        upload_date: Optional[str] = None,
        duration: Optional[str] = None,
        content_url: Optional[str] = None,
        embed_url: Optional[str] = None,
        transcript: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate VideoObject schema.

        Args:
            name: Video title
            description: Video description
            thumbnail_url: Thumbnail image URL
            upload_date: ISO date string
            duration: ISO 8601 duration (e.g., "PT15M")
            content_url: Direct video URL
            embed_url: Embeddable URL
            transcript: Video transcript

        Returns:
            VideoObject schema dictionary
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            "name": name,
        }

        if description:
            schema["description"] = description
        if thumbnail_url:
            schema["thumbnailUrl"] = thumbnail_url
        if upload_date:
            schema["uploadDate"] = upload_date
        if duration:
            schema["duration"] = duration
        if content_url:
            schema["contentUrl"] = content_url
        if embed_url:
            schema["embedUrl"] = embed_url
        if transcript:
            schema["transcript"] = transcript[:5000]  # Reasonable limit

        return schema


class CourseSchemaGenerator:
    """Generate Course/LearningResource schema for educational content."""

    def generate_course(
        self,
        name: str,
        description: str,
        provider: Optional[str] = None,
        course_code: Optional[str] = None,
        educational_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate Course schema for educational articles."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Course",
            "name": name,
            "description": description[:500],
        }

        if provider:
            schema["provider"] = {
                "@type": "Organization",
                "name": provider,
            }

        return schema


class ProductSchemaGenerator:
    """Generate Product/Review schema for affiliate/commercial content."""

    def generate_product(
        self,
        name: str,
        description: str,
        brand: Optional[str] = None,
        offers: Optional[Dict[str, Any]] = None,
        review_rating: Optional[Dict[str, Any]] = None,
        aggregate_rating: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate Product schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": name,
            "description": description[:500],
        }

        if brand:
            schema["brand"] = {"@type": "Brand", "name": brand}

        if offers:
            schema["offers"] = offers

        if aggregate_rating:
            schema["aggregateRating"] = aggregate_rating

        return schema