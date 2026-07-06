#!/usr/bin/env python3
"""
Blogger Automation Platform - Entry Point.

ARCHITECTURAL DECISION: Application Entry Point Pattern
-------------------------------------------------------
This module serves as the application entry point with a clean CLI.
It follows the "Thin Controller" pattern:

1. Parse user input (CLI arguments)
2. Wire together dependencies (authenticator, client)
3. Call the appropriate business logic
4. Present results to user

It does NOT contain business logic - that lives in core/ and other modules.
This separation makes the system:
- Testable (business logic can be tested without CLI)
- Reusable (same logic can be called from web dashboard in Phase 7)
- Maintainable (clear separation of concerns)
"""

from datetime import datetime, timedelta
from pathlib import Path

import structlog
from typing_extensions import Annotated

# For now, we'll use a simple CLI. In Phase 7, this becomes a web dashboard.
# Install with: pip install typer[all]
import json

try:
    import typer
    from typer import Typer
except ImportError:
    typer = None  # type: ignore
    Typer = None  # type: ignore

from config import get_settings, setup_logging, get_logger
from core.auth import Authenticator
from core.blogger_client import BloggerClient
from core.models import BlogPost, PostStatus
from core.publishing import Publisher, RetryConfig, PublishQueue
from ai.generator import AIArticleGenerator
from ai.seo_title import SEOTitleGenerator
from ai.meta_optimizer import MetaDescriptionOptimizer
from ai.faq_generator import FAQGenerator
from ai.summary_generator import SummaryGenerator
from ai.keyword_optimizer import KeywordOptimizer

# Initialize CLI app
if typer and Typer:
    app = Typer(
        name="blogger-automation",
        help="Production-grade Blogger Automation Platform",
        no_args_is_help=True,
    )
else:
    app = None


def main() -> None:
    """Main entry point - runs a quick test of the platform."""
    # Load and apply configuration
    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        log_file_path=settings.log_file_path,
    )

    logger = get_logger("app")
    logger.info("Starting Blogger Automation Platform")

    # Quick validation
    try:
        authenticator = Authenticator()
        has_valid_creds = authenticator.validate_credentials()

        if has_valid_creds:
            logger.info("Authentication verified")
            print("✓ Authentication credentials are valid")
        else:
            logger.warning("No valid credentials found")
            print("✗ Please run 'python app.py auth' to authenticate")

        # Test client initialization
        client = BloggerClient()
        print(f"✓ Blogger client configured for blog ID: {settings.blogger_blog_id}")

    except Exception as e:
        logger.error("Startup error", error=str(e))
        print(f"✗ Error: {e}")
        raise


def create_sample_post() -> BlogPost:
    """Create a sample post for testing."""
    return BlogPost(
        title="Platform Test Post",
        content="<h1>Hello from Blogger Automation Platform</h1><p>This is a test post.</p>",
        labels=["test", "automation"],
    )


def demo_publish() -> None:
    """Demo function to publish a test post."""
    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        log_file_path=settings.log_file_path,
    )

    logger = get_logger("app")

    try:
        post = create_sample_post()
        client = BloggerClient()
        result = client.publish_post(post)

        if result.success:
            print(f"✓ Published post {result.post_id}")
            print(f"  URL: {result.url}")
        else:
            print(f"✗ Failed to publish: {result.error}")

    except Exception as e:
        logger.error("Demo publish failed", error=str(e))
        print(f"✗ Error: {e}")


# Typer CLI commands (when available)
if app:

    @app.command("auth")
    def authenticate() -> None:
        """Run OAuth authentication flow."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        authenticator = Authenticator()
        credentials = authenticator.load_credentials()

        print("✓ Authentication successful")
        print(f"  Credentials stored at: {settings.google_credentials_storage_path}")


    @app.command("list-blogs")
    def list_blogs() -> None:
        """List all accessible Blogger blogs."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        client = BloggerClient()
        blogs = client.list_blogs()

        print(f"Found {len(blogs)} blog(s):")
        for blog in blogs:
            print(f"  - {blog.name} ({blog.id})")
            print(f"    {blog.url}")


    @app.command("publish")
    def publish(
        title: Annotated[str, typer.Option(help="Post title")],
        content: Annotated[str, typer.Option(help="HTML content")] = "<p>Auto-generated content</p>",
        labels: Annotated[str, typer.Option(help="Comma-separated labels")] = "",
    ) -> None:
        """Publish a post to Blogger."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        labels_list = [l.strip() for l in labels.split(",") if l.strip()]

        post = BlogPost(
            title=title,
            content=content,
            labels=labels_list,
        )

        publisher = Publisher()
        result = publisher.publish(post)

        if result.success:
            print(f"✓ Published post {result.post_id}")
            print(f"  URL: {result.url}")
        else:
            print(f"✗ Failed: {result.error}")

    @app.command("schedule")
    def schedule(
        title: Annotated[str, typer.Option(help="Post title")],
        content: Annotated[str, typer.Option(help="HTML content")] = "<p>Auto-generated content</p>",
        labels: Annotated[str, typer.Option(help="Comma-separated labels")] = "",
        when: Annotated[str, typer.Option(help="ISO datetime or 'tomorrow'")] = None,
    ) -> None:
        """Schedule a post for future publishing."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        labels_list = [l.strip() for l in labels.split(",") if l.strip()]

        # Parse scheduling time
        if when == "tomorrow":
            scheduled_time = datetime.now() + timedelta(days=1)
        elif when:
            try:
                scheduled_time = datetime.fromisoformat(when)
            except ValueError:
                print(f"✗ Invalid datetime format: {when}")
                return
        else:
            print("✗ --when is required (ISO datetime or 'tomorrow')")
            return

        post = BlogPost(
            title=title,
            content=content,
            labels=labels_list,
        )

        publisher = Publisher()
        result = publisher.publish(post, schedule_time=scheduled_time)

        if result.success and result.is_scheduled:
            print(f"✓ Post scheduled (queue_id: {result.queue_id})")
            print(f"  Scheduled for: {scheduled_time.isoformat()}")
        else:
            print(f"✗ Failed: {result.error}")

    @app.command("bulk-publish")
    def bulk_publish(
        file: Annotated[Path, typer.Option(help="JSON file with posts array")] = None,
    ) -> None:
        """Publish multiple posts from a JSON file."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        if not file or not file.exists():
            print("✗ --file is required with JSON file path")
            return

        data = json.loads(file.read_text())
        posts = [BlogPost(**p) for p in data.get("posts", [])]

        publisher = Publisher()
        results = publisher.publish_bulk(posts)

        success_count = sum(1 for r in results if r.success)
        print(f"Published {success_count}/{len(posts)} posts successfully")

    @app.command("seo-check")
    def seo_check(
        title: Annotated[str, typer.Option(help="Post title")],
        content: Annotated[str, typer.Option(help="HTML content")] = "",
    ) -> None:
        """Check SEO quality of a post."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        from seo import SEOAnalyzer

        analyzer = SEOAnalyzer()
        report = analyzer.analyze(title, content)

        print(f"SEO Score: {report.overall_score}/100")
        print(f"  Title: {report.title_score.value}/100")
        print(f"  Meta: {report.meta_score.value}/100")
        print(f"  Headings: {report.heading_score.value}/100")
        print(f"  Keywords: {report.keyword_score.value}/100")
        print(f"  Readability: {report.readability_score.value}/100")

        if report.all_issues:
            print(f"\nIssues found:")
            for issue in report.all_issues[:5]:
                print(f"  - {issue}")

        if report.all_suggestions:
            print(f"\nSuggestions:")
            for sugg in report.all_suggestions[:5]:
                print(f"  - {sugg}")

    @app.command("ai-generate")
    def ai_generate(
        topic: Annotated[str, typer.Option(help="Article topic")] = None,
        tone: Annotated[str, typer.Option(help="Writing tone: professional, casual, technical, friendly")] = "professional",
        keywords: Annotated[str, typer.Option(help="Comma-separated target keywords")] = "",
        words: Annotated[int, typer.Option(help="Target word count")] = 1000,
        language: Annotated[str, typer.Option(help="Target language: en, kn, hi, es, fr, de, zh, ja, ta, te")] = "en",
        publish: Annotated[bool, typer.Option(help="Publish to Blogger after generation")] = False,
    ) -> None:
        """Generate an AI-powered blog post."""
        if not topic:
            print("✗ --topic is required")
            return

        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        keywords_list = [k.strip() for k in keywords.split(",") if k.strip()]

        try:
            generator = AIArticleGenerator()
            from ai.models import AIArticleRequest
            request = AIArticleRequest(
                topic=topic,
                target_keywords=keywords_list,
                tone=tone,
                word_count=words,
                language=language,
            )
            response = generator.generate(request)

            print(f"✓ Generated article")
            print(f"  Title: {response.title}")
            print(f"  Words: {response.word_count}")
            print(f"  SEO Score: {response.seo_score}/100")
            if language != "en":
                print(f"  Language: {language}")

            if response.meta_description:
                print(f"  Meta: {response.meta_description[:80]}...")

            if publish:
                from core.models import BlogPost
                post = BlogPost(
                    title=response.title,
                    content=response.content,
                    labels=keywords_list,
                )
                publisher = Publisher()
                result = publisher.publish(post)
                if result.success:
                    print(f"  ✓ Published: {result.url}")
                else:
                    print(f"  ✗ Publish failed: {result.error}")
            else:
                # Save to file
                output = {
                    "title": response.title,
                    "content": response.content,
                    "meta_description": response.meta_description,
                    "keywords": response.target_keywords,
                }
                output_path = Path("data/generated_post.json")
                output_path.parent.mkdir(exist_ok=True)
                output_path.write_text(json.dumps(output, indent=2))
                print(f"  Saved to: {output_path}")

        except Exception as e:
            print(f"✗ Error: {e}")

    @app.command("ai-title")
    def ai_title(
        topic: Annotated[str, typer.Option(help="Article topic")] = None,
        keywords: Annotated[str, typer.Option(help="Comma-separated keywords")] = "",
        language: Annotated[str, typer.Option(help="Target language: en, kn, hi, es, fr, de, zh, ja, ta, te")] = "en",
    ) -> None:
        """Generate SEO-optimized title variants."""
        if not topic:
            print("✗ --topic is required")
            return

        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        keywords_list = [k.strip() for k in keywords.split(",") if k.strip()]

        try:
            generator = SEOTitleGenerator()
            from ai.models import SEOTitleRequest
            request = SEOTitleRequest(
                topic=topic,
                target_keywords=keywords_list,
                language=language,
            )
            response = generator.generate(request)

            print(f"✓ Generated SEO title")
            print(f"  Title: {response.title}")
            print(f"  SEO Score: {response.seo_score}/100")
            print(f"  Keyword Coverage: {response.keyword_coverage}%")

        except Exception as e:
            print(f"✗ Error: {e}")

    @app.command("ai-meta")
    def ai_meta(
        title: Annotated[str, typer.Option(help="Post title")] = None,
        content: Annotated[str, typer.Option(help="Post content")] = "",
        keyword: Annotated[str, typer.Option(help="Target keyword")] = None,
    ) -> None:
        """Generate optimized meta description."""
        if not title:
            print("✗ --title is required")
            return

        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        try:
            optimizer = MetaDescriptionOptimizer()
            from ai.models import MetaOptimizationRequest
            request = MetaOptimizationRequest(
                title=title,
                content=content or f"<p>{title}</p>",
                target_keyword=keyword,
            )
            response = optimizer.optimize(request)

            print(f"✓ Meta description optimized")
            print(f"  Original Score: {response.original_score}/100")
            print(f"  Optimized Score: {response.optimized_score}/100")
            print(f"  Characters: {response.character_count}")
            print(f"  Meta: {response.meta_description}")

        except Exception as e:
            print(f"✗ Error: {e}")

    @app.command("ai-faq")
    def ai_faq(
        title: Annotated[str, typer.Option(help="Post title")] = None,
        content: Annotated[str, typer.Option(help="Post content")] = "",
        count: Annotated[int, typer.Option(help="Number of questions")] = 5,
    ) -> None:
        """Generate FAQ from content."""
        if not content:
            print("✗ --content is required")
            return

        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        try:
            generator = FAQGenerator()
            from ai.models import FAQRequest
            request = FAQRequest(
                title=title or "FAQ",
                content=content,
                num_questions=count,
            )
            response = generator.generate(request)

            print(f"✓ Generated {len(response.faqs)} FAQs")
            for faq in response.faqs:
                print(f"  Q: {faq.question}")
                print(f"  A: {faq.answer[:60]}...")

        except Exception as e:
            print(f"✗ Error: {e}")

    @app.command("ai-summary")
    def ai_summary(
        content: Annotated[str, typer.Option(help="Content to summarize")] = None,
        style: Annotated[str, typer.Option(help="Summary style: brief, detailed, bullets")] = "brief",
    ) -> None:
        """Generate summary of content."""
        if not content:
            print("✗ --content is required")
            return

        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        try:
            generator = SummaryGenerator()
            from ai.models import SummaryRequest
            request = SummaryRequest(
                content=content,
                style=style,
            )
            response = generator.generate(request)

            print(f"✓ Generated summary ({response.summary_length} chars)")
            print(f"  {response.summary}")

        except Exception as e:
            print(f"✗ Error: {e}")

    @app.command("ai-keywords")
    def ai_keywords(
        topic: Annotated[str, typer.Option(help="Main topic")] = None,
        content: Annotated[str, typer.Option(help="Existing content to optimize")] = "",
        enhance: Annotated[bool, typer.Option(help="Enhance keyword density")] = False,
    ) -> None:
        """Optimize content for keywords."""
        if not topic:
            print("✗ --topic is required")
            return

        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        try:
            optimizer = KeywordOptimizer()
            from ai.models import KeywordOptimizationRequest
            request = KeywordOptimizationRequest(
                main_topic=topic,
                content=content or f"<p>Content about {topic}</p>",
                enhance_density=enhance,
            )
            response = optimizer.optimize(request)

            print(f"✓ Keyword analysis complete")
            print(f"  SEO Improvement: {response.seo_improvement}/100")
            print(f"  Related keywords: {len(response.suggestions)}")
            for kw in response.suggestions[:5]:
                print(f"    - {kw.keyword} (relevance: {kw.relevance})")

        except Exception as e:
            print(f"✗ Error: {e}")



    @app.command("update")
    def update_post(
        post_id: Annotated[str, typer.Option(help="Blogger post ID to update")],
        title: Annotated[str, typer.Option(help="New post title")] = None,
        content: Annotated[str, typer.Option(help="New HTML content")] = None,
        labels: Annotated[str, typer.Option(help="Comma-separated labels")] = None,
        status: Annotated[str, typer.Option(help="Post status: draft, published")] = None,
    ) -> None:
        """Update an existing blog post."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        from core.publishing import Publisher
        from core.blogger_client import BloggerClient
        
        publisher = Publisher()
        
        # First, fetch the existing post to preserve unchanged fields
        try:
            client = BloggerClient()
            existing_result = client.get_post(post_id)
            if not existing_result.success:
                print(f"✗ Failed to fetch existing post: {existing_result.error}")
                return
            
            # Extract data from raw_response (Blogger API response)
            raw = existing_result.raw_response
            current = BlogPost(
                title=raw.get('title'),
                content=raw.get('content'),
                labels=raw.get('labels', []),
            )
        except Exception as e:
            print(f"✗ Failed to fetch existing post: {e}")
            return

        # Update only the provided fields
        if title:
            current.title = title
        if content:
            current.content = content
        if labels:
            current.labels = [l.strip() for l in labels.split(",") if l.strip()]

        new_status = None
        if status:
            try:
                new_status = PostStatus(status.lower())
            except ValueError:
                print(f"✗ Invalid status: {status}. Use 'draft' or 'published'")
                return

        result = publisher.update_post(post_id, current, new_status)

        if result.success:
            print(f"✓ Updated post {result.post_id}")
            if result.url:
                print(f"  URL: {result.url}")
        else:
            print(f"✗ Failed to update: {result.error}")

    @app.command("delete")
    def delete_post(
        post_id: Annotated[str, typer.Option(help="Blogger post ID to delete")],
        confirm: Annotated[bool, typer.Option(help="Skip confirmation prompt")] = False,
    ) -> None:
        """Delete a blog post from Blogger."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        if not confirm:
            response = input(f"Are you sure you want to delete post {post_id}? (yes/no): ")
            if response.lower() != "yes":
                print("✗ Deletion cancelled")
                return

        from core.publishing import Publisher
        publisher = Publisher()
        result = publisher.delete_post(post_id)

        if result:
            print(f"✓ Post {post_id} deleted successfully")
        else:
            print(f"✗ Failed to delete post {post_id}")



if __name__ == "__main__":
    if app is None:
        # Fallback for when typer is not installed
        print("Running in simple mode (install typer for full CLI)")
        main()
    else:
        app()