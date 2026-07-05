"""
Blogger API client wrapper.

ARCHITECTURAL DECISION: Why wrap googleapiclient?
-------------------------------------------------
The googleapiclient.discovery.Build pattern is powerful but verbose.
This wrapper provides:

1. Method-per-operation (publish_post, update_post, etc.) instead of
   service.posts().insert(...).execute() everywhere

2. Automatic error handling and translation to our exceptions

3. Consistent return types (PostResult) instead of raw API responses

4. Built-in logging for debugging and audit trails

5. Future extensibility: easy to add retry logic, caching, metrics

Design pattern: Repository pattern (from Domain-Driven Design)
- Methods accept domain models (BlogPost)
- Methods return domain models or result types (PostResult)
- Hides implementation details (HTTP, authentication, JSON)
"""

from typing import List, Optional

from googleapiclient import discovery
from google.auth.credentials import Credentials
from googleapiclient.errors import HttpError

from config import get_settings, get_logger
from core.auth import Authenticator
from core.models import BlogPost, BlogInfo, PostResult, PostStatus
from core.exceptions import APIError, AuthenticationError, ValidationError

logger = get_logger("core", "blogger_client")


class BloggerClient:
    """
    Client for interacting with Blogger API v3.

    ARCHITECTURAL DECISION: Service discovery caching
    ------------------------------------------------
    We cache the service object after first build because:
    1. Discovery document fetch is expensive (network + parsing)
    2. Service object is thread-safe for concurrent requests
    3. Reduces latency for subsequent operations

    Trade-off: If Google updates their API, we'd need to re-discover.
    For production, consider adding a TTL or version check.
    """

    _service: Optional[discovery.Resource] = None

    def __init__(
        self,
        blog_id: Optional[str] = None,
        credentials: Optional[Credentials] = None,
    ) -> None:
        """
        Initialize Blogger client.

        Args:
            blog_id: Default blog ID for operations (defaults from settings)
            credentials: Optional pre-loaded credentials (tests or advanced usage)

        Note:
            If credentials not provided, Authenticator will be used.
        """
        settings = get_settings()
        self._blog_id = blog_id or settings.blogger_blog_id
        self._authenticator = Authenticator() if credentials is None else None
        self._credentials = credentials

        if not self._blog_id:
            raise ValidationError("No blog_id provided and not configured in settings")

        logger.info("BloggerClient initialized", blog_id=self._blog_id)

    def _get_service(self) -> discovery.Resource:
        """
        Get or build the Blogger API service object.

        Design decision: Lazy initialization - service is built on first use,
        not in __init__. This allows the client to be instantiated without
        immediately triggering OAuth flow.

        Returns:
            Authorized Blogger API service object
        """
        if self._service is None:
            if self._credentials is None:
                self._credentials = self._authenticator.load_credentials()

            if self._credentials is None:
                raise AuthenticationError("Failed to obtain valid credentials")

            self._service = discovery.build(
                "blogger",
                "v3",
                credentials=self._credentials,
                discoveryServiceUrl="https://blogger.googleapis.com/$discovery/rest?version=v3",
            )
            logger.debug("Built Blogger API service")

        return self._service

    def list_blogs(self) -> List[BlogInfo]:
        """
        List all blogs accessible with current credentials.

        Returns:
            List of BlogInfo objects for accessible blogs

        Raises:
            APIError: If the API call fails
        """
        service = self._get_service()

        try:
            response = service.blogs().listByUser().execute()
            blogs = [
                BlogInfo.from_api_response(blog)
                for blog in response.get("items", [])
            ]
            logger.info("Listed blogs", count=len(blogs))
            return blogs
        except HttpError as e:
            raise APIError(
                "Failed to list blogs",
                status_code=e.resp.status,
                response_body=self._parse_error_body(e),
            ) from e

    def publish_post(self, post: BlogPost) -> PostResult:
        """
        Publish a blog post (creates draft, scheduled, or published post).

        Args:
            post: BlogPost to publish

        Returns:
            PostResult with post_id and status

        Raises:
            ValidationError: If post is missing required fields
            APIError: If API call fails
        """
        self._validate_post(post)
        service = self._get_service()

        try:
            # Build the API request body
            body = self._build_post_body(post, PostStatus.PUBLISHED)

            response = (
                service.posts()
                .insert(blogId=self._blog_id, body=body, fetchImages=True)
                .execute()
            )

            logger.info(
                "Post published successfully",
                post_id=response.get("id"),
                title=post.title,
            )
            return PostResult.from_api_response(response, PostStatus.PUBLISHED)

        except HttpError as e:
            error_msg = f"Failed to publish post: {e}"
            logger.error(error_msg, status_code=e.resp.status)
            raise APIError(
                error_msg,
                status_code=e.resp.status,
                response_body=self._parse_error_body(e),
            ) from e

    def save_draft(self, post: BlogPost) -> PostResult:
        """
        Save a blog post as a draft.

        Args:
            post: BlogPost to save as draft

        Returns:
            PostResult with post_id (draft has no URL yet)
        """
        self._validate_post(post, require_published=False)
        service = self._get_service()

        try:
            body = self._build_post_body(post, PostStatus.DRAFT)

            response = (
                service.posts()
                .insert(blogId=self._blog_id, body=body)
                .execute()
            )

            logger.info("Draft saved successfully", post_id=response.get("id"))
            return PostResult.from_api_response(response, PostStatus.DRAFT)

        except HttpError as e:
            error_msg = f"Failed to save draft: {e}"
            logger.error(error_msg)
            raise APIError(
                error_msg,
                status_code=e.resp.status,
                response_body=self._parse_error_body(e),
            ) from e

    def update_post(
        self, post_id: str, post: BlogPost, status: Optional[PostStatus] = None
    ) -> PostResult:
        """
        Update an existing blog post.

        Args:
            post_id: The Blogger post ID to update
            post: Updated BlogPost data
            status: Optional status change (draft → published, etc.)

        Returns:
            PostResult with updated post info
        """
        service = self._get_service()

        try:
            body = self._build_post_body(post, status or PostStatus.PUBLISHED)

            response = (
                service.posts()
                .update(blogId=self._blog_id, postId=post_id, body=body)
                .execute()
            )

            logger.info("Post updated", post_id=post_id)
            return PostResult.from_api_response(response, status or PostStatus.PUBLISHED)

        except HttpError as e:
            error_msg = f"Failed to update post {post_id}: {e}"
            logger.error(error_msg)
            raise APIError(
                error_msg,
                status_code=e.resp.status,
                response_body=self._parse_error_body(e),
            ) from e

    def get_post(self, post_id: str) -> PostResult:
        """
        Retrieve an existing blog post by ID.

        Args:
            post_id: The Blogger post ID to retrieve

        Returns:
            PostResult with post details

        Raises:
            APIError: If the API call fails
        """
        service = self._get_service()

        try:
            response = (
                service.posts()
                .get(blogId=self._blog_id, postId=post_id)
                .execute()
            )

            logger.info("Post retrieved", post_id=post_id)
            return PostResult.from_api_response(response)

        except HttpError as e:
            error_msg = f"Failed to get post {post_id}: {e}"
            logger.error(error_msg)
            raise APIError(
                error_msg,
                status_code=e.resp.status,
                response_body=self._parse_error_body(e),
            ) from e

    def delete_post(self, post_id: str) -> bool:
        """
        Delete a blog post.

        Args:
            post_id: The Blogger post ID to delete

        Returns:
            True if deletion was successful
        """
        service = self._get_service()

        try:
            service.posts().delete(blogId=self._blog_id, postId=post_id).execute()
            logger.info("Post deleted", post_id=post_id)
            return True
        except HttpError as e:
            error_msg = f"Failed to delete post {post_id}: {e}"
            logger.error(error_msg)
            raise APIError(
                error_msg,
                status_code=e.resp.status,
                response_body=self._parse_error_body(e),
            ) from e

    def schedule_post(self, post: BlogPost) -> PostResult:
        """
        Schedule a post for future publishing.

        Args:
            post: BlogPost with published datetime set

        Returns:
            PostResult with scheduled status

        Note: The post.published field must be set to a future datetime.
        """
        if post.published is None:
            raise ValidationError("Scheduled posts require a published datetime")

        self._validate_post(post)
        service = self._get_service()

        try:
            body = self._build_post_body(post, PostStatus.SCHEDULED)

            response = (
                service.posts()
                .insert(blogId=self._blog_id, body=body)
                .execute()
            )

            logger.info(
                "Post scheduled",
                post_id=response.get("id"),
                publish_time=post.published.isoformat(),
            )
            return PostResult.from_api_response(response, PostStatus.SCHEDULED)

        except HttpError as e:
            error_msg = f"Failed to schedule post: {e}"
            logger.error(error_msg)
            raise APIError(
                error_msg,
                status_code=e.resp.status,
                response_body=self._parse_error_body(e),
            ) from e

    def _validate_post(self, post: BlogPost, require_published: bool = True) -> None:
        """Validate post has required fields."""
        if require_published and not post.is_valid_for_publish():
            raise ValidationError(
                "Post missing required fields for publishing",
                details={"title_present": bool(post.title), "content_present": bool(post.content)},
            )

    def _build_post_body(
        self, post: BlogPost, status: PostStatus
    ) -> dict:
        """
        Build the API request body from BlogPost model.

        Design decision: This conversion is isolated so we can:
        1. Change API format without changing BlogPost
        2. Add field transformations/validation here
        3. Log what's being sent to API for debugging

        Note: Blogger API uses 'content' for HTML body, not 'html'
        """
        body = {
            "title": post.title,
            "content": post.content,
            "labels": post.labels,
        }

        if status == PostStatus.SCHEDULED and post.published:
            body["published"] = post.published.isoformat()
        elif status == PostStatus.DRAFT:
            body["status"] = "draft"

        logger.debug("Building post body", post_id=post.title, status=status.value)
        return body

    def _parse_error_body(self, error: HttpError) -> dict:
        """Parse HTTP error response body for logging."""
        try:
            return error.error_details if hasattr(error, "error_details") else {}
        except Exception:
            return {"raw_error": str(error)}