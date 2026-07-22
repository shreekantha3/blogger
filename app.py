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



@app.command("analytics-top-queries")
    def analytics_top_queries(
        days: Annotated[int, typer.Option(help="Number of days")] = 90,
        limit: Annotated[int, typer.Option(help="Max queries to return")] = 100,
    ) -> None:
        """Get top performing search queries."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        from analytics.gsc_client import GSCClient
        client = GSCClient()
        queries = client.get_top_queries(days=days, row_limit=limit)

        print(f"Top {len(queries)} queries (last {days} days):")
        for q in queries[:20]:
            print(f"  {q.query}: {q.clicks} clicks, {q.ctr:.1%} CTR, #{q.position:.0f}")

    @app.command("analytics-audit")
    def analytics_audit(
        detect_decaying: Annotated[bool, typer.Option(help="Find decaying posts")] = True,
        decaying_threshold: Annotated[float, typer.Option(help="Traffic drop % threshold")] = 20.0,
    ) -> None:
        """Run content audit to find stale/decaying posts."""
        settings = get_settings()
        setup_logging(
            level=settings.log_level,
            log_format=settings.log_format,
            log_file_path=settings.log_file_path,
        )

        from analytics.content_audit import run_audit
        report = run_audit(traffic_drop_threshold=decaying_threshold)

        print(f"# Content Audit Report - {report.generated_at.strftime('%Y-%m-%d')}")
        print(f"\nTotal issues found: {report.total_issues}")

        if report.priority_updates:
            print(f"\n## Priority Updates ({len(report.priority_updates)})")
            for post in report.priority_updates[:5]:
                print(f"  - {post.title}: {post.traffic_drop_pct:.1f}% drop")

        if report.refresh_candidates:
            print(f"\n## Refresh Candidates ({len(report.refresh_candidates)})")
            for post in report.refresh_candidates[:5]:
                print(f"  - {post.title}: {post.days_since_update} days since update")

    @app.command("schema-job")
    def schema_job(
        title: Annotated[str, typer.Option(help="Job title")] = None,
        date: Annotated[str, typer.Option(help="Date posted (YYYY-MM-DD)")] = None,
    ) -> None:
        """Generate JobPosting schema for recruitment articles."""
        if not title:
            print("✗ --title is required")
            return

        from ai.schema_howto import JobPostingSchemaGenerator
        generator = JobPostingSchemaGenerator()

        # Generate with minimal required data
        schema = generator.generate_jobposting(
            title=title,
            date_posted=date or datetime.now().strftime("%Y-%m-%d"),
        )

        print("```json")
        print(json.dumps(schema, indent=2))
        print("```")

    @app.command("schema-howto")
    def schema_howto(
        title: Annotated[str, typer.Option(help="How-to title")] = None,
        steps: Annotated[str, typer.Option(help="JSON array of steps")] = '[]',
    ) -> None:
        """Generate HowTo schema for tutorial articles."""
        if not title:
            print("✗ --title is required")
            return

        from ai.schema_howto import HowToSchemaGenerator
        generator = HowToSchemaGenerator()

        try:
            steps_list = json.loads(steps)
        except json.JSONDecodeError:
            print("✗ Invalid JSON for steps")
            return

        schema = generator.generate_howto(title=title, steps=steps_list)

        print("```json")
        print(json.dumps(schema, indent=2))
        print("```")

    @app.command("content-brief")
    def content_brief(
        topic: Annotated[str, typer.Option(help="Article topic")] = None,
        keyword: Annotated[str, typer.Option(help="Target keyword")] = None,
    ) -> None:
        """Generate content brief with SERP insights."""
        if not topic or not keyword:
            print("✗ Both --topic and --keyword are required")
            return

        import asyncio
        from ai.content_brief import ContentBriefGenerator, ContentBriefRequest
        generator = ContentBriefGenerator()
        request = ContentBriefRequest(
            topic=topic,
            target_keyword=keyword or topic,
        )
        brief = asyncio.run(generator.generate(request))

        print(brief.formatted_brief)

    @app.command("serp-analyze")
    def serp_analyze(
        keyword: Annotated[str, typer.Option(help="Target keyword")] = None,
        location: Annotated[str, typer.Option(help="Location code (IN, US, etc.)")] = "IN",
    ) -> None:
        """Analyze SERP for content strategy insights."""
        if not keyword:
            print("✗ --keyword is required")
            return

        import asyncio
        from seo.serp_analyzer import SERPAnalyzer
        analyzer = SERPAnalyzer()
        brief = asyncio.run(analyzer.analyze(keyword, location=location))

        print(f"Search Intent: {brief.search_intent}")
        print(f"Recommended Word Count: {brief.recommended_word_count}")
        print(f"\nTop PAA Questions:")
        for q in brief.paa_questions[:5]:
            print(f"  - {q}")
        print(f"\nContent Gaps to Exploit:")
        for gap in brief.content_gaps:
            print(f"  - {gap}")

    @app.command("ai-image")
    def ai_image(
        type: Annotated[str, typer.Option(help="Image type: feature, diagram, chart")] = "feature",
        title: Annotated[str, typer.Option(help="Title/topic for image")] = None,
        topic: Annotated[str, typer.Option(help="Article topic")] = None,
        chart_type: Annotated[str, typer.Option(help="Chart type: bar, line, pie")] = "bar",
        data: Annotated[str, typer.Option(help="JSON data for charts/diagrams")] = "{}",
    ) -> None:
        """Generate AI-powered images for blog posts."""
        if not title:
            print("✗ --title is required")
            return

        import asyncio
        from media.ai_image_generator import AIImageGenerator

        generator = AIImageGenerator()

        try:
            if type == "feature":
                result = asyncio.run(
                    generator.generate_feature_image(
                        title=title,
                        topic=topic or title,
                    )
                )
            elif type == "diagram":
                data_dict = json.loads(data) if data else {}
                result = asyncio.run(
                    generator.generate_diagram(
                        concept=title,
                        data=data_dict,
                    )
                )
            elif type == "chart":
                data_dict = json.loads(data) if data else {}
                result = asyncio.run(
                    generator.generate_chart(
                        chart_type=chart_type,
                        data=data_dict,
                        title=title,
                    )
                )
            else:
                print(f"✗ Invalid type: {type}. Use 'feature', 'diagram', or 'chart'")
                return

            if result.error:
                print(f"✗ Generation failed: {result.error}")
            elif result.url:
                print(f"✓ Generated image")
                print(f"  URL: {result.url}")
                if result.revised_prompt:
                    print(f"  Revised prompt: {result.revised_prompt[:80]}...")

        except json.JSONDecodeError:
            print("✗ Invalid JSON for --data")
        except Exception as e:
            print(f"✗ Error: {e}")

    @app.command("keywords-research")
    def keywords_research(
        seed: Annotated[str, typer.Option(help="Seed keyword to research")] = None,
        easy_wins: Annotated[bool, typer.Option(help="Show only easy wins")] = False,
        limit: Annotated[int, typer.Option(help="Max keywords to return")] = 50,
    ) -> None:
        """Research keyword opportunities."""
        if not seed:
            print("✗ --seed is required")
            return

        from seo.keyword_research import KeywordResearcher, find_easy_wins
        researcher = KeywordResearcher()
        opportunities = researcher.find_opportunities(seed, limit=limit)

        if easy_wins:
            opportunities = find_easy_wins(opportunities)

        print(f"Found {len(opportunities)} keyword opportunities for '{seed}':")
        print()

        for kw in opportunities[:20]:
            score = researcher._opportunity_score(kw)
            print(f"  {kw.keyword}")
            print(f"    Volume: {kw.search_volume:,} | Difficulty: {kw.difficulty:.0f} | Score: {score:.0f}")
            print(f"    Intent: {kw.intent}")
            print()

    @app.command("internal-links")
    def internal_links(
        topic: Annotated[str, typer.Option(help="Topic to find links for")] = None,
        top_k: Annotated[int, typer.Option(help="Max links to return")] = 5,
    ) -> None:
        """Analyze internal link graph and suggest links."""
        from ai.internal_link_graph import InternalLinkGraph
        from ai.internal_linking import InternalLinkSuggester

        # For now, use the existing suggester
        suggester = InternalLinkSuggester()

        # Mock existing posts - in production would fetch from Blogger
        mock_posts = [
            {"id": "1", "title": "KSP Recruitment 2026", "content": "police exam", "url": "/ksp-2026", "keywords": ["police", "recruitment"]},
            {"id": "2", "title": "CCI Recruitment 2026", "content": "insurance exam", "url": "/cci-2026", "keywords": ["insurance", "recruitment"]},
        ]

        print("Internal Link Analysis")
        print("=" * 50)

        if topic:
            links = suggester.find_related_posts(
                current_content=f"<p>Content about {topic}</p>",
                target_keywords=[topic],
                existing_posts=mock_posts,
            )
            print(f"Suggested links for '{topic}':")
            for link in links[:top_k]:
                print(f"  - {link.anchor_text} → {link.url} (score: {link.relevance_score:.2f})")

        print(f"\nRecommendation: {suggester.get_link_density_recommendation(1000)}")


if __name__ == "__main__":
    if app is None:
        # Fallback for when typer is not installed
        print("Running in simple mode (install typer for full CLI)")
        main()
    else:
        app()