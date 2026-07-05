"""
Core domain models for Blogger Automation Platform.

ARCHITECTURAL DECISION: Immutability and Validation
----------------------------------------------------
We use dataclasses with frozen=False (mutable) for BlogPost because:
1. Blog posts evolve through a workflow (draft → scheduled → published)
2. Fields like 'labels' or 'content' may be added incrementally
3. Mutability is needed for the builder pattern

However, we use `field(default_factory=...)` for mutable defaults (lists, dicts)
to avoid the classic Python pitfall of shared mutable defaults.

Design pattern: Data Transfer Object (DTO)
- Clean separation between internal representation and API format
- Easy to extend with computed properties
- Type-safe access throughout the application
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class PostStatus(str, Enum):
    """
    Status of a blog post in the Blogger system.

    ARCHITECTURAL DECISION: String enum vs Int enum
    ---------------------------------------------
    We use str enums because:
    1. They serialize cleanly to JSON for API calls
    2. They're human-readable in logs and debugging
    3. They match Blogger API's own status values
    """

    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"


@dataclass
class BlogPost:
    """
    Domain entity representing a blog post.

    This is the primary model for creating and updating posts.
    All fields are optional to allow partial updates.

    Attributes:
        title: Post title (required for publishing)
        content: HTML content of the post
        labels: List of tags/categories for the post
        author: Display name for the author (if different from blog default)
        published: When the post should be published (None for draft)
    """

    title: Optional[str] = None
    content: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    author: Optional[str] = None
    published: Optional[datetime] = None
    # Future fields for Phase 2+:
    # images: list[ImageAsset] = field(default_factory=list)
    # seo_metadata: SEOMetadata = field(default_factory=SEOMetadata)

    def is_valid_for_publish(self) -> bool:
        """
        Check if post has minimum required fields for publishing.

        Design decision: Validation in the model keeps it close to the data.
        This is a simple check - comprehensive validation happens in Phase 3 (SEO).
        """
        return bool(self.title and self.content)


@dataclass
class PostResult:
    """
    Result of a Blogger API operation.

    ARCHITECTURAL DECISION: Result pattern
    ---------------------------------------
    Instead of returning raw API responses, we wrap them in a result object.
    This provides:
    1. Consistent return type across all operations
    2. Success/failure indication without exception handling
    3. Access to both the returned post and metadata

    Attributes:
        success: Whether the operation succeeded
        post_id: The Blogger post ID (None if failed)
        url: Public URL of the post (None if draft/failed)
        status: The post status after the operation
        error: Error message if success is False
        raw_response: Full API response for debugging
    """

    success: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    status: Optional[PostStatus] = None
    error: Optional[str] = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_response(
        cls,
        response: dict[str, Any],
        status: PostStatus = PostStatus.PUBLISHED,
    ) -> "PostResult":
        """
        Create a PostResult from a Blogger API response.

        The API returns different structures for different operations,
        so we normalize them here.
        """
        return cls(
            success=True,
            post_id=str(response.get("id", "")),
            url=response.get("url"),
            status=PostStatus(status),
            raw_response=response,
        )

    @classmethod
    def failure(cls, error: str, details: Optional[dict[str, Any]] = None) -> "PostResult":
        """Create a failed result with error message."""
        return cls(
            success=False,
            error=error,
            raw_response=details or {},
        )


@dataclass
class BlogInfo:
    """
    Information about a Blogger blog.

    Used for listing blogs and validating configuration.

    Attributes:
        id: Unique blog identifier
        name: Blog display name
        url: Blog URL
    """

    id: str
    name: str
    url: str

    @classmethod
    def from_api_response(cls, response: dict[str, Any]) -> "BlogInfo":
        """Create BlogInfo from API response."""
        return cls(
            id=str(response.get("id", "")),
            name=response.get("name", ""),
            url=response.get("url", ""),
        )