"""Tests for Phase 2 Publishing Engine."""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

from core.publishing.retry import (
    RetryStrategy,
    RetryConfig,
    RetryPolicy,
    exponential_backoff,
)
from core.publishing.queue import PublishQueue, QueuedPost, QueueStatus
from core.publishing.publisher import Publisher, PublishResult
from core.models import BlogPost, PostResult, PostStatus


class TestExponentialBackoff:
    """Tests for exponential backoff delay calculation."""

    def test_first_attempt_uses_base_delay(self) -> None:
        """First retry should use base delay."""
        delay = exponential_backoff(attempt=0, base_delay=1.0, multiplier=2.0, max_delay=60.0)
        assert delay == 1.0

    def test_second_attempt_doubles_delay(self) -> None:
        """Second retry doubles the delay."""
        delay = exponential_backoff(attempt=1, base_delay=1.0, multiplier=2.0, max_delay=60.0)
        assert delay == 2.0

    def test_delay_caps_at_max(self) -> None:
        """Delay should not exceed max_delay."""
        delay = exponential_backoff(attempt=10, base_delay=1.0, multiplier=2.0, max_delay=60.0)
        assert delay == 60.0  # Capped at max


class TestPublishQueue:
    """Tests for PublishQueue."""

    def test_queue_add_and_get(self) -> None:
        """Test adding and retrieving queued posts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = PublishQueue(storage_path=Path(tmpdir) / "queue.json")
            post = BlogPost(title="Test", content="<p>Test</p>")
            queued = queue.add(post)

            assert len(queue._items) == 1
            assert queued.status == QueueStatus.QUEUED
            assert queued.post_data["title"] == "Test"

    def test_queue_mark_published(self) -> None:
        """Test marking a post as published."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = PublishQueue(storage_path=Path(tmpdir) / "queue.json")
            post = BlogPost(title="Test", content="<p>Test</p>")
            queued = queue.add(post)

            queue.mark_published(queued.id, "12345")

            updated = queue.get_by_id(queued.id)
            assert updated is not None
            assert updated.status == QueueStatus.PUBLISHED
            assert updated.post_id == "12345"


class TestPublisher:
    """Tests for Publisher class."""

    def test_publisher_uses_retry_strategy(self) -> None:
        """Test that Publisher uses RetryStrategy for API calls."""
        mock_client = MagicMock()
        mock_client.publish_post.return_value = PostResult(success=True, post_id="123")

        publisher = Publisher(client=mock_client)

        post = BlogPost(title="Test", content="<p>Test</p>")
        result = publisher.publish(post)

        assert result.success
        assert result.post_id == "123"
        mock_client.publish_post.assert_called_once()

    def test_publisher_scheduled_post(self) -> None:
        """Test scheduling a post returns queue_id."""
        mock_client = MagicMock()

        publisher = Publisher(client=mock_client)

        post = BlogPost(title="Test", content="<p>Test</p>")
        schedule_time = datetime.now(timezone.utc) + timedelta(days=1)
        result = publisher.publish(post, schedule_time=schedule_time)

        assert result.is_scheduled
        assert result.queue_id is not None
        mock_client.publish_post.assert_not_called()

class TestBloggerClientGetPost:
    """Tests for BloggerClient.get_post method."""

    def test_get_post_success(self) -> None:
        """Test retrieving a post by ID."""
        from core.blogger_client import BloggerClient
        
        mock_client = MagicMock()
        mock_client.get_post.return_value = PostResult(
            success=True,
            post_id="12345",
            url="https://example.com/post",
            raw_response={
                "id": "12345",
                "title": "Test Post",
                "content": "<p>Test content</p>",
                "labels": ["test", "example"]
            }
        )
        
        result = mock_client.get_post("12345")
        
        assert result.success
        assert result.post_id == "12345"

    def test_get_post_not_found(self) -> None:
        """Test retrieving a non-existent post."""
        from core.blogger_client import BloggerClient
        from core.exceptions import APIError
        
        mock_client = MagicMock()
        mock_client.get_post.side_effect = APIError("Post not found", status_code=404)
        
        try:
            mock_client.get_post("nonexistent")
            assert False, "Should have raised APIError"
        except APIError as e:
            assert e.status_code == 404


class TestPublisherUpdatePost:
    """Tests for Publisher.update_post method."""

    def test_update_post_title_only(self) -> None:
        """Test updating only the title preserves other fields."""
        mock_client = MagicMock()
        mock_client.get_post.return_value = PostResult(
            success=True,
            post_id="123",
            raw_response={
                "id": "123",
                "title": "Old Title",
                "content": "<p>Original content</p>",
                "labels": ["old-label"]
            }
        )
        mock_client.update_post.return_value = PostResult(
            success=True,
            post_id="123",
            url="https://example.com/post"
        )

        publisher = Publisher(client=mock_client)
        
        # First fetch existing post
        existing = mock_client.get_post("123")
        
        # Create updated post with new title only
        from core.models import BlogPost
        updated_post = BlogPost(
            title="New Title",  # Updated
            content=existing.raw_response["content"],  # Preserved
            labels=existing.raw_response["labels"],  # Preserved
        )
        
        result = publisher.update_post("123", updated_post)
        
        assert result.success
        mock_client.update_post.assert_called_once()

    def test_update_post_content(self) -> None:
        """Test updating post content."""
        mock_client = MagicMock()
        mock_client.update_post.return_value = PostResult(
            success=True,
            post_id="456",
            url="https://example.com/new-content"
        )

        publisher = Publisher(client=mock_client)
        
        from core.models import BlogPost
        post = BlogPost(title="Test", content="<p>New content</p>")
        result = publisher.update_post("456", post)
        
        assert result.success
        assert result.post_id == "456"


class TestPublisherDeletePost:
    """Tests for Publisher.delete_post method."""

    def test_delete_post_success(self) -> None:
        """Test successful post deletion."""
        mock_client = MagicMock()
        mock_client.delete_post.return_value = True

        publisher = Publisher(client=mock_client)
        result = publisher.delete_post("12345")
        
        assert result is True
        mock_client.delete_post.assert_called_once_with("12345")

    def test_delete_post_failure(self) -> None:
        """Test post deletion failure."""
        mock_client = MagicMock()
        mock_client.delete_post.side_effect = Exception("Delete failed")

        publisher = Publisher(client=mock_client)
        result = publisher.delete_post("12345")
        
        assert result is False
