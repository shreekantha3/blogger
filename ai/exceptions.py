"""
AI Engine exception hierarchy.

ARCHITECTURAL DECISION: Exception Per Module Pattern
----------------------------------------------------
Following the same pattern as core/exceptions.py, we provide
AI-specific exceptions that inherit from BloggerAutomationError.

This allows:
1. Specific error handling for AI operations
2. Differentiating AI failures from other errors
3. Clear recovery strategies per error type
"""

from typing import Any, Optional

from core.exceptions import BloggerAutomationError


class AIEngineError(BloggerAutomationError):
    """
    Base exception for all AI Engine errors.

    All AI-related exceptions inherit from this class.
    This allows catching just AI errors without interfering with
    other platform errors.
    """

    pass


class AIServiceError(AIEngineError):
    """
    Raised when the LLM service is unavailable or misconfigured.

    This could happen due to:
    - Missing or invalid API key
    - Network connectivity issues
    - Service rate limiting or downtime
    - Invalid model name

    Recovery strategy:
    - Check configuration (API key, model)
    - Wait and retry with exponential backoff
    - Fall back to alternative provider
    """

    pass


class AIContentError(AIEngineError):
    """
    Raised when AI-generated content fails validation.

    This could happen due to:
    - Content too short or too long
    - Missing required elements
    - Inappropriate content flagged by safety filters

    Recovery strategy:
    - Regenerate with adjusted parameters
    - Adjust temperature/retry counts
    """

    pass


class AITitleError(AIEngineError):
    """Raised when SEO title generation fails."""

    pass


class AIMetaError(AIEngineError):
    """Raised when meta description optimization fails."""

    pass


class AIFAQError(AIEngineError):
    """Raised when FAQ generation fails."""

    pass


class AISummaryError(AIEngineError):
    """Raised when summary generation fails."""

    pass


class AIKeywordError(AIEngineError):
    """Raised when keyword optimization fails."""

    pass