"""
Publishing Engine for Blogger Automation Platform.

ARCHITECTURAL DECISION: Module Organization
-------------------------------------------
This is a sub-module under core/ because publishing is core business logic.
Separate from blogger_client.py which handles raw API calls.

This module adds business logic like:
- Retry strategies
- Rate limiting
- Bulk operations
- Scheduling queues
"""

from core.publishing.publisher import Publisher
from core.publishing.retry import RetryStrategy, exponential_backoff, RetryConfig
from core.publishing.queue import PublishQueue

__all__ = [
    "Publisher",
    "RetryStrategy",
    "RetryConfig",
    "exponential_backoff",
    "PublishQueue",
]