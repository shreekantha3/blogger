"""
Schema Markup Generator for SEO Enhancement.

ARCHITECTURAL DECISION: Schema Generation Module
-------------------------------------------------
This module generates JSON-LD structured data for:
1. Article/BlogPosting schema - for rich results in Google Search
2. BreadcrumbList schema - for breadcrumb navigation
3. HowTo schema - for tutorial/how-to content with steps
4. Combined output for all markup types

Based on RankMath SEO recommendations and Google's guidelines.

Usage:
    from ai.schema_generator import SchemaGenerator

    generator = SchemaGenerator()
    article_schema = generator.generate_article_schema(
        title="Post Title",
        content="<h1>Content</h1><p>...</p>",
        keywords=["python", "seo"],
        author="Author Name",
        publish_date="2025-01-01",
        image_url="https://example.com/image.jpg"
    )
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class HowToStep:
    """Represents a single step in a HowTo guide."""

    def __init__(
        self,
        name: str,
        text: str,
        url: Optional[str] = None,
        image: Optional[str] = None,
    ) -> None:
        self.name = name
        self.text = text
        self.url = url
        self.image = image

    def to_dict(self) -> Dict[str, Any]:
        """Convert to schema.org HowToStep format."""
        step: Dict[str, Any] = {
            "@type": "HowToStep",
            "name": self.name,
            "text": self.text,
        }
        if self.url:
            step["url"] = self.url
        if self.image:
            step["image"] = self.image
        return step


class SchemaGenerator:
    """
    Generates JSON-LD schema markup for SEO optimization.

    Supports Article/BlogPosting, BreadcrumbList, and HowTo schemas.
    """

    def generate_article_schema(
        self,
        title: str,
        content: str,
        keywords: Optional[List[str]] = None,
        author: Optional[str] = None,
        publish_date: Optional[str] = None,
        image_url: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate Article/BlogPosting JSON-LD schema.

        Args:
            title: Article title
            content: HTML content (used to extract description if not provided)
            keywords: List of keywords/tags
            author: Author name
            publish_date: ISO format date string (YYYY-MM-DD)
            image_url: URL to featured image
            description: Meta description (extracted from content if not provided)
            url: Article URL

        Returns:
            Dictionary containing the Article schema

        Example:
            >>> schema = generator.generate_article_schema(
            ...     title="Python Tips",
            ...     content="<p>Content...</p>",
            ...     keywords=["python", "programming"],
            ...     author="John Doe",
            ...     publish_date="2025-01-15"
            ... )
            >>> print(json.dumps(schema, indent=2))
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
        }

        # Add description
        if description:
            schema["description"] = description[:160]  # Max 160 chars
        elif content:
            # Extract text from content for description
            import re
            text = re.sub(r'<[^>]+>', '', content)
            text = re.sub(r'\s+', ' ', text).strip()
            schema["description"] = text[:160]

        # Add author
        if author:
            schema["author"] = {
                "@type": "Person",
                "name": author
            }

        # Add publish date
        if publish_date:
            try:
                # Validate date format
                datetime.strptime(publish_date, "%Y-%m-%d")
                schema["datePublished"] = publish_date
            except ValueError:
                pass  # Skip if invalid date

        # Add image
        if image_url:
            schema["image"] = image_url

        # Add keywords
        if keywords:
            schema["keywords"] = ", ".join(keywords[:10])  # Max 10 keywords

        # Add URL
        if url:
            schema["mainEntityOfPage"] = {
                "@type": "WebPage",
                "@id": url
            }

        return schema

    def generate_breadcrumb_schema(
        self,
        breadcrumb_list: List[Dict[str, str]],
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate BreadcrumbList JSON-LD schema.

        Args:
            breadcrumb_list: List of dicts with 'name' and 'url' keys
                            Example: [{"name": "Home", "url": "/"}, {"name": "Blog", "url": "/blog"}]
            base_url: Base URL for the site (prepended to relative URLs)

        Returns:
            Dictionary containing the BreadcrumbList schema

        Example:
            >>> breadcrumbs = [
            ...     {"name": "Home", "url": "/"},
            ...     {"name": "Blog", "url": "/blog"},
            ...     {"name": "Python Guide", "url": "/blog/python-guide"}
            ... ]
            >>> schema = generator.generate_breadcrumb_schema(breadcrumbs)
        """
        items = []
        for i, item in enumerate(breadcrumb_list, 1):
            breadcrumb_item = {
                "@type": "ListItem",
                "position": i,
                "name": item.get("name", ""),
            }

            url = item.get("url", "")
            if url and base_url:
                # Ensure URL is absolute
                if url.startswith("/"):
                    url = base_url.rstrip("/") + url
            elif url:
                url = base_url.rstrip("/") + "/" + url if base_url else url

            if url:
                breadcrumb_item["item"] = url

            items.append(breadcrumb_item)

        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": items
        }

    def generate_howto_schema(
        self,
        title: str,
        steps: Optional[List[HowToStep]] = None,
        total_time: Optional[str] = None,
        tool: Optional[str] = None,
        image_url: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate HowTo schema for tutorial content.

        HowTo schema helps content appear in rich results with step-by-step instructions.

        Args:
            title: The title of the HowTo guide
            steps: List of HowToStep objects representing each step
            total_time: ISO 8601 duration (e.g., "PT30M" for 30 minutes)
            tool: Required tool or material for the HowTo
            image_url: Featured image URL
            description: Meta description

        Returns:
            Dictionary containing the HowTo schema

        Example:
            >>> steps = [
            ...     HowToStep(name="Step 1", text="First step description"),
            ...     HowToStep(name="Step 2", text="Second step description"),
            ... ]
            >>> schema = generator.generate_howto_schema(
            ...     title="How to Install Python",
            ...     steps=steps,
            ...     total_time="PT15M",
            ... )
        """
        schema: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": title,
        }

        if description:
            schema["description"] = description[:160]
        elif steps:
            # Use first step as description if none provided
            schema["description"] = steps[0].text[:160]

        if image_url:
            schema["image"] = image_url

        if total_time:
            schema["totalTime"] = total_time

        if tool:
            schema["tool"] = tool

        if steps:
            schema["step"] = [step.to_dict() for step in steps]

        return schema

    def combine_schemas(self, *schemas: Dict[str, Any]) -> str:
        """
        Combine multiple schema objects into a single JSON-LD script.

        Args:
            *schemas: Variable number of schema dictionaries

        Returns:
            JSON string containing all schemas

        Example:
            >>> article = generator.generate_article_schema(...)
            >>> breadcrumbs = generator.generate_breadcrumb_schema(...)
            >>> combined = generator.combine_schemas(article, breadcrumbs)
        """
        if len(schemas) == 1:
            return json.dumps(schemas[0], indent=2)

        return json.dumps(list(schemas), indent=2)

    def generate_all_schemas(
        self,
        title: str,
        content: str,
        keywords: Optional[List[str]] = None,
        author: Optional[str] = None,
        publish_date: Optional[str] = None,
        image_url: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        breadcrumb_list: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate all schema markup for an article.

        This is a convenience method that combines Article and Breadcrumb schemas.

        Args:
            title: Article title
            content: HTML content
            keywords: List of keywords
            author: Author name
            publish_date: Publication date
            image_url: Featured image URL
            description: Meta description
            url: Article URL
            breadcrumb_list: Breadcrumb navigation items

        Returns:
            Dictionary with 'article', 'breadcrumb', and 'combined' keys
        """
        article_schema = self.generate_article_schema(
            title=title,
            content=content,
            keywords=keywords,
            author=author,
            publish_date=publish_date,
            image_url=image_url,
            description=description,
            url=url,
        )

        breadcrumb_schema = None
        if breadcrumb_list:
            base_url = url.split("/blog")[0] if url else None
            breadcrumb_schema = self.generate_breadcrumb_schema(
                breadcrumb_list=breadcrumb_list,
                base_url=base_url,
            )

        return {
            "article": article_schema,
            "breadcrumb": breadcrumb_schema,
            "combined": self.combine_schemas(
                article_schema,
                *(breadcrumb_schema,) if breadcrumb_schema else ()
            ),
        }

    def validate_schema(self, schema: Dict[str, Any]) -> bool:
        """
        Validate a schema dictionary has required fields.

        Args:
            schema: Schema dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(schema, dict):
            return False

        if "@context" not in schema or "@type" not in schema:
            return False

        return True

    def get_schema_html(self, schema: Dict[str, Any]) -> str:
        """
        Generate HTML script tag with JSON-LD schema.

        Args:
            schema: Schema dictionary

        Returns:
            HTML script tag string
        """
        json_ld = json.dumps(schema, indent=2)
        return f'<script type="application/ld+json">\n{json_ld}\n</script>'
