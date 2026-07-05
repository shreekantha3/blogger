"""
Publish queue for managing scheduled posts.

ARCHITECTURAL DECISION: Simple JSON-based queue
-----------------------------------------------
We use JSON file storage instead of Redis/PostgreSQL because:

1. Phase 1-2 scope: This is a desktop tool, not a distributed system
2. Simplicity: No external dependencies for core functionality
3. Reliability: File-based storage is predictable and debuggable
4. Cost: No infrastructure needed

FUTURE: In Phase 7, we'll migrate to async queue (Celery/RQ) for
the web dashboard, with backward-compatible API.

KEY DESIGN DECISION: Status field
---------------------------------
Each queued item tracks its state:
- queued: Waiting to be processed
- publishing: Currently being published
- published: Successfully published (post_id recorded)
- failed: Failed after retries (error recorded)
- cancelled: Removed before publishing
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from config import get_settings, get_logger
from core.models import BlogPost, PostStatus

logger = get_logger("core", "publishing", "queue")


class QueueStatus(str):
    """Status of a queued post."""

    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueuedPost:
    """
    A post scheduled for future publishing.

    Design decision: We store the original BlogPost as a dict in the
    queue for serialization. This allows full reconstruction later.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    scheduled_time: str = ""  # ISO format datetime string
    status: str = QueueStatus.QUEUED
    post_data: dict = field(default_factory=dict)
    post_id: Optional[str] = None  # Blogger post ID after publishing
    error: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def from_blog_post(cls, post: BlogPost, scheduled_time: datetime) -> "QueuedPost":
        """Create QueuedPost from BlogPost model."""
        return cls(
            scheduled_time=scheduled_time.isoformat(),
            post_data={
                "title": post.title,
                "content": post.content,
                "labels": post.labels,
                "author": post.author,
                "published": post.published.isoformat() if post.published else None,
            },
        )

    def to_blog_post(self) -> BlogPost:
        """Reconstruct BlogPost from queued data."""
        post_data = self.post_data
        published_str = post_data.get("published")
        published = None
        if published_str:
            try:
                published = datetime.fromisoformat(published_str)
            except (ValueError, TypeError):
                pass

        return BlogPost(
            title=post_data.get("title"),
            content=post_data.get("content"),
            labels=post_data.get("labels", []),
            author=post_data.get("author"),
            published=published,
        )


class PublishQueue:
    """
    Manages a queue of posts waiting to be published.

    ARCHITECTURAL DECISION: Active Record pattern
    --------------------------------------------
    The queue manages its own persistence to JSON. This is simpler than
    a Repository pattern for this use case. For multi-user scenarios,
    we'd migrate to database-backed storage.
    """

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        settings = get_settings()
        self._storage_path = storage_path or Path("data/publish_queue.json")
        self._items: list[QueuedPost] = []
        self._load()

    def _load(self) -> None:
        """Load queue from storage file."""
        if not self._storage_path.exists():
            self._items = []
            return

        try:
            data = json.loads(self._storage_path.read_text())
            self._items = [QueuedPost(**item) for item in data]
            logger.debug(f"Loaded {len(self._items)} items from queue")
        except Exception as e:
            logger.error(f"Failed to load queue: {e}")
            self._items = []

    def _save(self) -> None:
        """Persist queue to storage file."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(item) for item in self._items]
        self._storage_path.write_text(json.dumps(data, indent=2))
        logger.debug(f"Saved {len(self._items)} items to queue")

    def add(
        self,
        post: BlogPost,
        scheduled_time: Optional[datetime] = None,
    ) -> QueuedPost:
        """
        Add a post to the queue for publishing.

        If scheduled_time is None, publishes immediately.
        """
        # Default to immediate publishing
        if scheduled_time is None:
            scheduled_time = datetime.now(timezone.utc)

        queued_post = QueuedPost.from_blog_post(post, scheduled_time)
        self._items.append(queued_post)
        self._save()

        logger.info(
            "Added post to queue",
            queue_id=queued_post.id,
            scheduled_for=queued_post.scheduled_time,
        )
        return queued_post

    def get_pending(self) -> list[QueuedPost]:
        """Get posts ready for publishing (scheduled time has passed)."""
        now = datetime.now(timezone.utc)
        return [
            item
            for item in self._items
            if item.status == QueueStatus.QUEUED
            and datetime.fromisoformat(item.scheduled_time) <= now
        ]

    def get_all(self) -> list[QueuedPost]:
        """Get all queued posts."""
        return list(self._items)

    def get_by_id(self, queue_id: str) -> Optional[QueuedPost]:
        """Get a specific queued post by ID."""
        for item in self._items:
            if item.id == queue_id:
                return item
        return None

    def mark_publishing(self, queue_id: str) -> None:
        """Mark a post as currently being published."""
        item = self.get_by_id(queue_id)
        if item:
            item.status = QueueStatus.PUBLISHING
            self._save()

    def mark_published(self, queue_id: str, post_id: str) -> None:
        """Mark a post as successfully published."""
        item = self.get_by_id(queue_id)
        if item:
            item.status = QueueStatus.PUBLISHED
            item.post_id = post_id
            self._save()

    def mark_failed(self, queue_id: str, error: str) -> None:
        """Mark a post as failed."""
        item = self.get_by_id(queue_id)
        if item:
            item.status = QueueStatus.FAILED
            item.error = error
            self._save()

    def remove(self, queue_id: str) -> bool:
        """
        Remove a post from the queue.

        Returns True if removed, False if not found.
        """
        for i, item in enumerate(self._items):
            if item.id == queue_id:
                self._items.pop(i)
                self._save()
                logger.info("Removed post from queue", queue_id=queue_id)
                return True
        return False

    def clear_completed(self) -> int:
        """Remove all published/failed/cancelled items. Returns count removed."""
        original_count = len(self._items)
        self._items = [
            item
            for item in self._items
            if item.status in (QueueStatus.QUEUED, QueueStatus.PUBLISHING)
        ]
        self._save()
        return original_count - len(self._items)