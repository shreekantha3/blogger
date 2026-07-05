"""Core module for Blogger Automation Platform.

This module contains the essential business logic:
- auth: Google OAuth authentication using modern google-auth library
- blogger_client: Wrapper for Blogger API operations
- publishing: Publishing engine with retry and queue management
- models: Core domain models and data structures
- exceptions: Custom exception hierarchy
"""

from core.auth import Authenticator
from core.blogger_client import BloggerClient
from core.models import BlogPost, PostStatus, PostResult
from core.exceptions import (
    BloggerAutomationError,
    AuthenticationError,
    APIError,
    ValidationError,
)
from core.publishing import (
    Publisher,
    RetryStrategy,
    RetryConfig,
    PublishQueue,
)

__all__ = [
    "Authenticator",
    "BloggerClient",
    "BlogPost",
    "PostStatus",
    "PostResult",
    "BloggerAutomationError",
    "AuthenticationError",
    "APIError",
    "ValidationError",
    "Publisher",
    "RetryStrategy",
    "RetryConfig",
    "PublishQueue",
]