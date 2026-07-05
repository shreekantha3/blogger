"""
Retry strategies for handling transient failures.

ARCHITECTURAL DECISION: Strategy Pattern for Retries
----------------------------------------------------
We use a callable strategy pattern because:

1. Different operations may need different retry policies
   - API calls: retry on 5xx errors
   - Rate limits: retry with longer delays
   - Invalid input: don't retry

2. Configuration-driven - policies can change without code changes

3. Easy to test: can inject mock delay functions

EXPonential BACKOFF explained:
- First retry: 1s (base_delay)
- Second retry: 2s (base_delay * multiplier)
- Third retry: 4s (base_delay * multiplier^2)
- This prevents thundering herd and gives services time to recover
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeVar

from config import get_logger

logger = get_logger("core", "publishing", "retry")

T = TypeVar("T")  # Generic return type for retryable operations


class RetryPolicy(str, Enum):
    """
    Retry policies for different error scenarios.

    Design decision: We distinguish between transient (retryable) and
    permanent (non-retryable) errors. This prevents infinite retry loops
    on invalid input.
    """

    IMMEDIATE = "immediate"  # No retry
    EXPONENTIAL = "exponential"  # Gradual backoff
    FIXED = "fixed"  # Consistent delay


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of attempts (including first try)
        policy: Retry policy to use
        base_delay: Initial delay in seconds (for exponential backoff)
        max_delay: Maximum delay cap in seconds
        multiplier: Backoff multiplier (default 2.0)
    """

    max_attempts: int = 3
    policy: RetryPolicy = RetryPolicy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0


def exponential_backoff(
    attempt: int, base_delay: float, multiplier: float, max_delay: float
) -> float:
    """
    Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Initial delay in seconds
        multiplier: Backoff multiplier
        max_delay: Maximum delay cap

    Returns:
        Delay in seconds for this attempt

    Example:
        >>> exponential_backoff(0, 1.0, 2.0, 60.0)
        1.0
        >>> exponential_backoff(1, 1.0, 2.0, 60.0)
        2.0
        >>> exponential_backoff(5, 1.0, 2.0, 60.0)
        32.0
    """
    delay = base_delay * (multiplier**attempt)
    return min(delay, max_delay)


class RetryStrategy:
    """
    Executes operations with retry logic.

    ARCHITECTURAL DECISION: Class vs function
    -----------------------------------------
    We use a class because:
    1. Stateful - tracks attempts and total delay
    2. Reusable - can be injected into Publisher
    3. Testable - each method can be unit tested independently
    4. Extensible - can add metrics, logging hooks

    Usage:
        strategy = RetryStrategy(config=RetryConfig())
        result = strategy.execute(lambda: api_call())
    """

    def __init__(self, config: RetryConfig | None = None) -> None:
        self.config = config or RetryConfig()

    def execute(
        self,
        operation: Callable[[], T],
        is_retryable: Callable[[Exception], bool] | None = None,
    ) -> T:
        """
        Execute an operation with retry logic.

        Args:
            operation: Callable to execute (may raise exceptions)
            is_retryable: Function to determine if exception is retryable
                         (default: retries on APIError with 5xx status)

        Returns:
            Result from successful operation

        Raises:
            Last exception if all attempts fail
        """
        # Default: retry on server errors (5xx) and network issues
        if is_retryable is None:
            from core.exceptions import APIError

            def is_retryable(exc: Exception) -> bool:
                if isinstance(exc, APIError):
                    return 500 <= exc.status_code < 600
                return False

        last_exception: Exception | None = None

        for attempt in range(self.config.max_attempts):
            try:
                result = operation()
                if attempt > 0:
                    logger.info(
                        "Operation succeeded after retry",
                        attempts=attempt + 1,
                    )
                return result

            except Exception as e:
                last_exception = e

                if not is_retryable(e):
                    # Don't retry for client errors or validation issues
                    logger.warning(
                        "Non-retryable error, aborting",
                        error=str(e),
                        attempt=attempt + 1,
                    )
                    raise

                if attempt < self.config.max_attempts - 1:
                    delay = exponential_backoff(
                        attempt=attempt,
                        base_delay=self.config.base_delay,
                        multiplier=self.config.multiplier,
                        max_delay=self.config.max_delay,
                    )

                    logger.warning(
                        "Operation failed, retrying",
                        error=str(e),
                        attempt=attempt + 1,
                        max_attempts=self.config.max_attempts,
                        delay_seconds=delay,
                    )
                    time.sleep(delay)

        # All attempts failed
        logger.error(
            "All retry attempts exhausted",
            error=str(last_exception),
            max_attempts=self.config.max_attempts,
        )
        raise last_exception