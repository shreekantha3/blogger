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
import yaml

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


    @app.command("image-optimize")
    def image_optimize(
        input: Annotated[Path, typer.Option(help="Input image path")] = None,
        output: Annotated[Path, typer.Option(help="Output image path")] = None,
        quality: Annotated[int, typer.Option(help="JPEG/WebP quality (1-100)")] = 85,
    ) -> None:
        """Optimize an image for web publishing."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        if not input or not input.exists():
            print("✗ --input is required with valid image path")
            return

        try:
            from media.image_processor import ImageProcessor, ImageOptimizationConfig
            config = ImageOptimizationConfig(quality=quality)
            processor = ImageProcessor(config)
            result = processor.optimize_image(input, output)

            output_path = output or input.parent / f"{input.stem}_optimized{input.suffix}"
            print(f"✓ Optimized image")
            print(f"  Original: {input.stat().st_size} bytes")
            print(f"  Optimized: {len(result)} bytes")
            print(f"  Saved to: {output_path}")

        except ImportError:
            print("✗ Pillow not installed. Install with: pip install pillow")
        except Exception as e:
            print(f"✗ Error: {e}")


    @app.command("thumbnail")
    def generate_thumbnail(
        title: Annotated[str, typer.Option(help="Thumbnail title text")] = None,
        output: Annotated[Path, typer.Option(help="Output path for thumbnail")] = None,
        type: Annotated[str, typer.Option(help="Thumbnail type: og, twitter, square")] = "og",
        background: Annotated[Path, typer.Option(help="Background image path")] = None,
    ) -> None:
        """Generate social media thumbnail for blog post."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        if not title:
            print("✗ --title is required for thumbnail text")
            return

        if not output:
            print("✗ --output is required for thumbnail path")
            return

        try:
            from media.thumbnail_generator import ThumbnailGenerator
            generator = ThumbnailGenerator()

            output.parent.mkdir(parents=True, exist_ok=True)

            if type == "og":
                generator.generate_og_thumbnail(title, output, background)
            elif type == "twitter":
                generator.generate_twitter_thumbnail(title, output)
            elif type == "square":
                generator.generate_square_thumbnail(title, output)
            else:
                print(f"✗ Invalid type: {type}. Use 'og', 'twitter', or 'square'")
                return

            print(f"✓ Generated {type} thumbnail")
            print(f"  Size: {output.stat().st_size} bytes")

        except ImportError:
            print("✗ Pillow not installed. Install with: pip install pillow")
        except Exception as e:
            print(f"✗ Error: {e}")


    @app.command("images-suggest")
    def images_suggest(
        topic: Annotated[str, typer.Option(help="Article topic")] = None,
        count: Annotated[int, typer.Option(help="Number of images")] = 4,
        format: Annotated[bool, typer.Option(help="Output as HTML")] = False,
    ) -> None:
        """Suggest images with alt text for blog post."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        if not topic:
            print("✗ --topic is required")
            return

        try:
            from media.image_selector import ImageSelector
            selector = ImageSelector()
            suggestions = selector.suggest_images(topic=topic, count=count)

            print(f"✓ Generated {len(suggestions)} image suggestions")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion.url}")
                print(f"     Alt: {suggestion.alt_text}")

                if format:
                    print(f"     HTML: {suggestion.to_html()}")

        except Exception as e:
            print(f"✗ Error: {e}")


    @app.command("eeat-score")
    def eeat_score(
        title: Annotated[str, typer.Option(help="Post title")] = None,
        content: Annotated[str, typer.Option(help="Post content")] = "",
    ) -> None:
        """Score content for EEAT (Experience, Expertise, Authoritativeness, Trustworthiness)."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        if not title or not content:
            print("✗ --title and --content are required")
            return

        try:
            from seo.quality_scorer import QualityScorer
            scorer = QualityScorer()
            score = scorer.score_content(title, content)
            report = scorer.generate_eeat_report(content, title)

            grade = report["grade"]
            overall = report["overall_score"]

            print(f"✓ EEAT Score: {overall}/100 (Grade: {grade})")
            print(f"  Experience: {score.experience}/100")
            print(f"  Expertise: {score.expertise}/100")
            print(f"  Authoritativeness: {score.authoritativeness}/100")
            print(f"  Trustworthiness: {score.trustworthiness}/100")

            if report["issues"]:
                print(f"\n  Issues:")
                for issue in report["issues"]:
                    print(f"    - {issue}")

            if report["suggestions"]:
                print(f"\n  Suggestions:")
                for suggestion in report["suggestions"]:
                    print(f"    - {suggestion}")

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

    @app.command("list-posts")
    def list_posts(
        status: Annotated[str, typer.Option(help="Filter by status: draft, published, scheduled")] = None,
        limit: Annotated[int, typer.Option(help="Maximum posts to retrieve")] = 20,
    ) -> None:
        """List existing posts from the configured blog."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        client = BloggerClient()
        posts = client.list_posts(status=status, max_results=limit)

        if not posts:
            print("No posts found")
            return

        print(f"Found {len(posts)} post(s):")
        for post in posts:
            status_str = post.status.value if post.status else "unknown"
            # Truncate title for clean display
            title_display = post.raw_response.get("title", "Untitled")
            if len(title_display) > 50:
                title_display = title_display[:47] + "..."
            print(f"  {post.post_id}: \"{title_display}\" ({status_str})")
            if post.url:
                print(f"    {post.url}")

    @app.command("seo-audit")
    def seo_audit(
        max_results: Annotated[int, typer.Option(help="Maximum posts to analyze")] = 50,
        sort_by: Annotated[str, typer.Option(help="Sort order: worst, best, date")] = "worst",
    ) -> None:
        """Audit all published posts and show SEO scores sorted by performance."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        from seo import SEOAnalyzer

        client = BloggerClient()
        analyzer = SEOAnalyzer()

        # Get published posts only
        posts = client.list_posts(status="published", max_results=max_results)

        if not posts:
            print("No published posts found to audit")
            return

        print(f"Analyzing {len(posts)} post(s)...")

        # Analyze each post
        audit_results = []
        for i, post in enumerate(posts, 1):
            if i % 5 == 0:
                print(f"  Progress: {i}/{len(posts)}")

            try:
                title = post.raw_response.get("title", "")
                content = post.raw_response.get("content", "")
                report = analyzer.analyze(title, content)

                audit_results.append({
                    "post_id": post.post_id,
                    "title": title,
                    "url": post.url,
                    "score": report.overall_score,
                    "issues": report.all_issues,
                    "suggestions": report.all_suggestions,
                })
            except Exception as e:
                print(f"  Warning: Failed to analyze post {post.post_id}: {e}")

        # Sort by score
        if sort_by == "worst":
            audit_results.sort(key=lambda x: x["score"])
        elif sort_by == "best":
            audit_results.sort(key=lambda x: x["score"], reverse=True)

        print(f"\n{'='*60}")
        print("SEO AUDIT RESULTS")
        print(f"{'='*60}\n")

        for i, result in enumerate(audit_results[:20], 1):  # Show top 20
            score_display = f"{result['score']:3d}/100"
            title = result["title"][:45] + "..." if len(result["title"]) > 45 else result["title"]
            print(f"{i}. [{score_display}] {title}")
            if result["url"]:
                print(f"   {result['url']}")
            if result["issues"]:
                print(f"   Issues: {len(result['issues'])}")
            print()

        # Summary
        if audit_results:
            avg_score = sum(r["score"] for r in audit_results) / len(audit_results)
            print(f"Average SEO Score: {avg_score:.1f}/100")
            print(f"Posts audited: {len(audit_results)}")

    @app.command("accounts")
    def accounts() -> None:
        """List all configured Blogger accounts."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        from core.accounts import AccountManager

        manager = AccountManager()
        accs = manager.list_accounts()

        print(f"Configured Blogger accounts:")
        for acc in accs:
            valid = "✓" if manager.validate_account(acc.name) else "✗"
            print(f"  {valid} {acc.name}")
            print(f"    Blog ID: {acc.blog_id}")
            print(f"    Credentials: {acc.credentials_path}")
            if acc.labels:
                print(f"    Default labels: {', '.join(acc.labels)}")

    @app.command("account-add")
    def account_add(
        name: Annotated[str, typer.Option(help="Account identifier")] = None,
        blog_id: Annotated[str, typer.Option(help="Blogger blog ID")] = None,
    ) -> None:
        """
        Add a new Blogger account via OAuth flow.

        This will run the OAuth flow and save credentials to a new file.
        """
        if not name:
            print("✗ --name is required for account identifier")
            return

        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        from core.accounts import AccountManager

        manager = AccountManager()

        # Run OAuth flow for this account
        credentials_path = f"credentials_{name}.json"
        print(f"Starting OAuth flow for account '{name}'...")
        print(f"Credentials will be saved to: {credentials_path}")

        authenticator = Authenticator(credentials_path=Path(credentials_path))

        try:
            credentials = authenticator.load_credentials()
            print("✓ OAuth successful")

            # Create client and list blogs to verify
            client = BloggerClient(credentials=credentials, blog_id=blog_id)
            blogs = client.list_blogs()

            if blogs and not blog_id:
                print(f"\nAvailable blogs:")
                for i, blog in enumerate(blogs, 1):
                    print(f"  {i}. {blog.name} ({blog.id})")
                print(f"\nRun again with --blog-id <ID> to select a blog")
            elif blogs and blog_id:
                print(f"\n✓ Account '{name}' configured for blog: {blog_id}")
                print(f"  Add to config/accounts.yaml manually or edit after running")

                # Suggest YAML entry
                print(f"\nSuggested accounts.yaml entry:")
                print(f"  - name: {name}")
                print(f"    blog_id: \"{blog_id}\"")
                print(f"    credentials_path: \"{credentials_path}\"")

        except Exception as e:
            print(f"✗ OAuth failed: {e}")
            # Clean up failed credentials file
            try:
                Path(credentials_path).unlink()
            except Exception:
                pass

    @app.command("publish-to")
    def publish_to(
        account: Annotated[str, typer.Option(help="Account name to publish to")] = "default",
        title: Annotated[str, typer.Option(help="Post title")] = None,
        content: Annotated[str, typer.Option(help="HTML content")] = "<p>Auto-generated content</p>",
        labels: Annotated[str, typer.Option(help="Comma-separated labels")] = "",
    ) -> None:
        """Publish a post to a specific Blogger account."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        if not title:
            print("✗ --title is required")
            return

        from core.accounts import AccountManager

        manager = AccountManager()

        try:
            client = manager.get_client(account)
        except Exception as e:
            print(f"✗ Failed to get client for account '{account}': {e}")
            print("  Run 'python app.py accounts' to see available accounts")
            return

        labels_list = [l.strip() for l in labels.split(",") if l.strip()]

        post = BlogPost(
            title=title,
            content=content,
            labels=labels_list,
        )

        try:
            result = client.publish_post(post)
            if result.success:
                print(f"✓ Published post {result.post_id}")
                print(f"  URL: {result.url}")
                print(f"  Account: {account}")
            else:
                print(f"✗ Failed: {result.error}")
        except Exception as e:
            print(f"✗ Failed: {e}")

    @app.command("post-optimize")
    def post_optimize(
        post_id: Annotated[str, typer.Option(help="Blogger post ID to optimize")] = None,
        auto_fix: Annotated[bool, typer.Option(help="Automatically apply AI suggestions and update")] = False,
        dry_run: Annotated[bool, typer.Option(help="Preview changes without updating")] = True,
    ) -> None:
        """
        Fetch existing post, analyze SEO, generate improvements, and optionally update.

        Use --auto-fix to apply AI-generated improvements automatically.
        Use --dry-run to preview changes (default is preview mode).
        """
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        if not post_id:
            print("✗ --post-id is required")
            return

        client = BloggerClient()

        # Fetch existing post
        try:
            result = client.get_post(post_id)
            if not result.success:
                print(f"✗ Failed to fetch post: {result.error}")
                return
        except Exception as e:
            print(f"✗ Failed to fetch post: {e}")
            return

        raw = result.raw_response
        current_title = raw.get("title", "")
        current_content = raw.get("content", "")
        current_labels = raw.get("labels", [])

        print(f"Analyzing post: {current_title[:50]}...")

        # Run SEO analysis
        from seo import SEOAnalyzer
        analyzer = SEOAnalyzer()
        report = analyzer.analyze(current_title, current_content)

        print(f"\nCurrent SEO Score: {report.overall_score}/100")
        print(f"  Title: {report.title_score.value}/100")
        print(f"  Meta: {report.meta_score.value}/100")
        print(f"  Headings: {report.heading_score.value}/100")
        print(f"  Keywords: {report.keyword_score.value}/100")
        print(f"  Readability: {report.readability_score.value}/100")

        # Generate AI improvements
        if current_content:
            from ai.seo_title import SEOTitleGenerator
            from ai.meta_optimizer import MetaDescriptionOptimizer
            from ai.keyword_optimizer import KeywordOptimizer

            # Generate better title
            try:
                title_gen = SEOTitleGenerator()
                from ai.models import SEOTitleRequest
                # Extract topics from content for title generation
                content_preview = current_content[:200]
                title_request = SEOTitleRequest(
                    topic=current_title,
                    target_keywords=current_labels[:3],
                    language="en",
                )
                title_response = title_gen.generate(title_request)
                improved_title = title_response.title
                print(f"\n✓ Improved title suggestion ({title_response.seo_score}/100):")
                print(f"  {improved_title}")
            except Exception as e:
                print(f"\n  Warning: Could not generate title: {e}")
                improved_title = current_title

            # Generate better meta description
            try:
                meta_opt = MetaDescriptionOptimizer()
                from ai.models import MetaOptimizationRequest
                meta_request = MetaOptimizationRequest(
                    title=current_title,
                    content=current_content,
                )
                meta_response = meta_opt.optimize(meta_request)
                print(f"\n✓ Improved meta ({meta_response.optimized_score}/100):")
                print(f"  {meta_response.meta_description}")
            except Exception as e:
                print(f"  Warning: Could not generate meta: {e}")
                meta_response = None

        # If auto-fix, update the post
        if auto_fix and not dry_run:
            from core.models import BlogPost
            from core.publishing import Publisher

            post = BlogPost(
                title=improved_title if 'improved_title' in dir() else current_title,
                content=current_content,
                labels=current_labels,
            )

            publisher = Publisher()
            update_result = publisher.update_post(post_id, post)

            if update_result.success:
                print(f"\n✓ Post updated successfully")
                print(f"  URL: {update_result.url}")
            else:
                print(f"\n✗ Failed to update: {update_result.error}")
        else:
            print("\nℹ Use --auto-fix to apply changes (without --dry-run)")

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