"""
Custom exception hierarchy for Blogger Automation Platform.

ARCHITECTURAL DECISION: Why custom exceptions?
-----------------------------------------------
In production code, catching generic exceptions like ValueError or RuntimeError is
problematic because:
1. They don't convey domain-specific meaning
2. You can't differentiate between "post not found" vs "invalid title"
3. Error recovery logic depends on exception type (e.g., retry on 5xx, not on 4xx)

This module provides a clean hierarchy following the "Exception Per Module" pattern.
Each module can raise its own specific exceptions while allowing upstream handlers
to catch broader categories.

Usage:
    try:
        client.publish_post(post)
    except AuthenticationError:
        # Handle auth issues - maybe refresh token
    except APIError as e:
        if e.status_code >= 500:
            # Retryable server error
        else:
            # Client error - fix and retry
    except BloggerAutomationError:
        # Catch-all for any platform error
"""

from typing import Any, Optional


class BloggerAutomationError(Exception):
    """
    Base exception for all Blogger Automation errors.

    All custom exceptions in this project inherit from this class.
    This allows catching just project errors without interfering with
    standard library or third-party exceptions.

    Attributes:
        message: Human-readable error description
        details: Optional additional context (dict for structured data)
    """

    def __init__(
        self, message: str, details: Optional[dict[str, Any]] = None
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AuthenticationError(BloggerAutomationError):
    """
    Raised when OAuth authentication fails or credentials are invalid.

    This could happen due to:
    - Missing client_secret.json
    - Expired refresh token
    - User revoked permissions
    - Network issues during token exchange

    Recovery strategy:
    - Prompt user to re-authenticate
    - Clear stored credentials and restart OAuth flow
    """

    pass


class APIError(BloggerAutomationError):
    """
    Raised when Blogger API returns an error response.

    Design decision: We include HTTP status code because it determines
    error handling strategy (retry vs fix vs abandon).

    Attributes:
        status_code: HTTP status code from the API response
        response_body: Raw response body for debugging
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: Optional[dict[str, Any]] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body or {}
        super().__init__(message, details)


class ValidationError(BloggerAutomationError):
    """
    Raised when input validation fails.

    This covers:
    - Invalid blog post structure
    - Missing required fields
    - Invalid HTML content
    - SEO validation failures (Phase 3)

    Unlike APIError, ValidationError indicates the caller should fix
    their input before retrying.
    """

    pass


class ConfigurationError(BloggerAutomationError):
    """
    Raised when required configuration is missing or invalid.

    This is raised early at startup to fail fast, preventing
    confusing errors later during operation.
    """

    pass