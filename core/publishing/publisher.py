"""
Main publishing orchestrator.

ARCHITECTURAL DECISION: Facade Pattern
--------------------------------------
The Publisher class acts as a Facade over multiple subsystems:
1. BloggerClient (raw API calls)
2. RetryStrategy (failure handling)
3. PublishQueue (scheduling management)

This provides a unified interface for all publishing operations while
allowing each subsystem to be developed and tested independently.

KEY PRINCIPLES:
- Single Responsibility: Each class does one thing well
- Dependency Injection: All components are injected (easy testing)
- Composability: Can be called from CLI, web, or scheduled jobs
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from config import get_settings, get_logger
from core.auth import Authenticator
from core.blogger_client import BloggerClient
from core.models import BlogPost, PostResult, PostStatus
from core.publishing.retry import RetryStrategy, RetryConfig
from core.publishing.queue import PublishQueue, QueuedPost
from media.thumbnail_generator import ThumbnailGenerator

logger = get_logger("core", "publishing")


@dataclass
class PublishResult:
    """
    Result of a publishing operation.

    ARCHITECTURAL DECISION: Separate result type
    -------------------------------------------
    We use a separate PublishResult instead of just PostResult because:
    1. It includes queue_id for scheduled posts
    2. It aggregates results for bulk publishing
    3. It tracks retry attempts and total time
    """

    success: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    queue_id: Optional[str] = None
    is_scheduled: bool = False
    error: Optional[str] = None
    attempts: int = 1


class Publisher:
    """
    Orchestration layer for all publishing operations.

    Design decisions:
    1. Lazy initialization of BloggerClient (doesn't trigger OAuth until needed)
    2. Configurable retry strategy (can disable for dry runs)
    3. Queue management built-in but optional
    """

    def __init__(
        self,
        client: Optional[BloggerClient] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        queue: Optional[PublishQueue] = None,
    ) -> None:
        """
        Initialize publisher with optional components.

        Use dependency injection for testing:
            publisher = Publisher(client=mock_client, retry_strategy=no_retry)
        """
        settings = get_settings()
        self._client = client
        self._retry_strategy = retry_strategy or RetryStrategy()
        self._queue = queue or PublishQueue()
        self._blog_id = settings.blogger_blog_id

    def _ensure_client(self) -> BloggerClient:
        """Lazy initialization of BloggerClient."""
        if self._client is None:
            authenticator = Authenticator()
            credentials = authenticator.load_credentials()
            self._client = BloggerClient(credentials=credentials)
        return self._client

    def publish(
        self,
        post: BlogPost,
        schedule_time: Optional[datetime] = None,
        thumbnail: bool = False,
        thumbnail_topic: Optional[str] = None,
    ) -> PublishResult:
        """
        Publish a single post immediately or schedule for later.

        Args:
            post: BlogPost to publish
            schedule_time: Optional future time for scheduled publishing
            thumbnail: Whether to generate and upload a thumbnail
            thumbnail_topic: Topic for thumbnail text (defaults to post title)

        Returns:
            PublishResult with post details
        """
        # If scheduled, add to queue and return
        if schedule_time:
            queued = self._queue.add(post, schedule_time)
            logger.info(
                "Post scheduled",
                queue_id=queued.id,
                scheduled_for=schedule_time.isoformat(),
            )
            return PublishResult(
                success=True,
                queue_id=queued.id,
                is_scheduled=True,
            )

        # Otherwise, publish immediately with retry
        client = self._ensure_client()

        try:
            # Generate thumbnail if requested
            if thumbnail:
                post = self._publish_with_thumbnail(post, thumbnail_topic, client)

            result = self._retry_strategy.execute(
                lambda: client.publish_post(post),
            )
            return PublishResult(
                success=True,
                post_id=result.post_id,
                url=result.url,
            )

        except Exception as e:
            logger.error("Publish failed", error=str(e))
            return PublishResult(
                success=False,
                error=str(e),
            )

    def _publish_with_thumbnail(
        self,
        post: BlogPost,
        thumbnail_topic: Optional[str],
        client: Optional[BloggerClient] = None,
    ) -> BlogPost:
        """
        Generate thumbnail and embed it in the post content.

        Uses Picsum Photos for reliable random thumbnails.
        Blogger's fetchImages=true will download and host the image.

        Args:
            post: BlogPost to enhance with thumbnail
            thumbnail_topic: Topic for thumbnail text (for alt/SEO)
            client: Authenticated BloggerClient (not used, kept for compatibility)

        Returns:
            Updated BlogPost with thumbnail embedded in content
        """
        topic = thumbnail_topic or post.title or "Article"

        # Use Picsum Photos (reliable random image service)
        # Use seed parameter for deterministic images per topic
        seed = abs(hash(topic)) % 1000
        picsum_url = f"https://picsum.photos/seed/{seed}/1200/630"

        # Create image HTML and prepend to content
        thumbnail_html = f'<img src="{picsum_url}" alt="{post.title}" width="1200" height="630">\n\n'
        post.content = thumbnail_html + (post.content or "")

        logger.info("Thumbnail embedded in post", url=picsum_url)
        return post

    def _select_texture(self, topic: str) -> Optional[Path]:
        """
        Select a texture from the textures folder based on topic hash.

        Args:
            topic: Article topic for hash-based selection

        Returns:
            Path to selected texture, or None for solid background
        """
        # Resolve textures directory (handles both normal and worktree execution)
        textures_dir = Path("/Users/shree/Desktop/blogger/media/textures")
        if not textures_dir.exists():
            # Fallback to relative path for normal execution
            textures_dir = Path("media/textures")

        if not textures_dir.exists():
            return None

        # Get all JPG files in textures folder
        textures = sorted(textures_dir.glob("*.jpg"))

        if not textures:
            return None

        # Hash-based selection for consistent texture per topic
        texture_index = hash(topic) % len(textures)
        return textures[texture_index]

    def save_draft(self, post: BlogPost) -> PublishResult:
        """
        Save a post as draft without publishing.

        Args:
            post: BlogPost to save as draft

        Returns:
            PublishResult with draft details (no URL until published)
        """
        client = self._ensure_client()

        try:
            result = self._retry_strategy.execute(
                lambda: client.save_draft(post),
            )
            return PublishResult(
                success=True,
                post_id=result.post_id,
                is_scheduled=False,
            )

        except Exception as e:
            logger.error("Draft save failed", error=str(e))
            return PublishResult(
                success=False,
                error=str(e),
            )

    def publish_bulk(
        self,
        posts: List[BlogPost],
        delay_between: float = 1.0,
    ) -> List[PublishResult]:
        """
        Publish multiple posts with rate limiting.

        ARCHITECTURAL DECISION: Sequential vs Parallel publishing
        ------------------------------------------------------
        We publish sequentially (not parallel) because:

        1. Google APIs have rate limits (Queries Per Second quotas)
        2. Sequential allows precise retry on individual failures
        3. Simpler error handling and rollback
        4. Could add parallel mode in Phase 7 with async/celery

        Args:
            posts: List of BlogPost to publish
            delay_between: Seconds to wait between posts (rate limiting)

        Returns:
            List of PublishResult (one per input post)
        """
        import time

        results: List[PublishResult] = []

        for i, post in enumerate(posts):
            # Rate limiting delay between posts
            if i > 0:
                logger.debug(
                    "Rate limiting delay",
                    seconds=delay_between,
                    post_number=i,
                )
                time.sleep(delay_between)

            result = self.publish(post)
            results.append(result)

            if result.success:
                logger.info(
                    "Bulk publish success",
                    post_title=post.title,
                    post_index=i,
                    total_posts=len(posts),
                )
            else:
                logger.warning(
                    "Bulk publish failed for post",
                    post_title=post.title,
                    error=result.error,
                )

        return results

    def process_queue(self) -> List[PublishResult]:
        """
        Process all pending posts in the queue.

        This is meant to be called:
        - On a schedule (cron job)
        - On application startup
        - From the web dashboard (Phase 7)

        Returns:
            List of PublishResult for processed posts

        Note: Scheduled posts (with future published datetime) are handled
        differently - they use schedule_post() instead of publish_post().
        """
        pending = self._queue.get_pending()
        results: List[PublishResult] = []

        for queued_post in pending:
            client = self._ensure_client()

            try:
                self._queue.mark_publishing(queued_post.id)

                post = queued_post.to_blog_post()

                # Check if this is a scheduled post (has future published datetime)
                if post.published and post.published > datetime.now(timezone.utc):
                    result = client.schedule_post(post)
                    is_scheduled = True
                else:
                    result = client.publish_post(post)
                    is_scheduled = False

                self._queue.mark_published(queued_post.id, result.post_id)
                results.append(
                    PublishResult(
                        success=True,
                        post_id=result.post_id,
                        url=result.url,
                        queue_id=queued_post.id,
                        is_scheduled=is_scheduled,
                    )
                )

            except Exception as e:
                self._queue.mark_failed(queued_post.id, str(e))
                results.append(
                    PublishResult(
                        success=False,
                        queue_id=queued_post.id,
                        error=str(e),
                    )
                )

        return results

    def cancel_scheduled(self, queue_id: str) -> bool:
        """Cancel a scheduled post. Returns True if found and cancelled."""
        return self._queue.remove(queue_id)
    def update_post(self, post_id: str, post: BlogPost, status: Optional[PostStatus] = None) -> PostResult:
        """
        Update an existing blog post.

        Args:
            post_id: The Blogger post ID to update
            post: Updated BlogPost data
            status: Optional status change (draft → published, etc.)

        Returns:
            PostResult with updated post info
        """
        client = self._ensure_client()

        try:
            result = client.update_post(post_id, post, status)
            logger.info(
                "Post updated via Publisher",
                post_id=post_id,
                status=status.value if status else "published",
            )
            return result

        except Exception as e:
            logger.error("Update failed", post_id=post_id, error=str(e))
            return PostResult.failure(str(e))

    def delete_post(self, post_id: str) -> bool:
        """
        Delete a blog post.

        Args:
            post_id: The Blogger post ID to delete

        Returns:
            True if deletion was successful
        """
        client = self._ensure_client()

        try:
            result = client.delete_post(post_id)
            logger.info("Post deleted via Publisher", post_id=post_id)
            return result

        except Exception as e:
            logger.error("Delete failed", post_id=post_id, error=str(e))
            return False
