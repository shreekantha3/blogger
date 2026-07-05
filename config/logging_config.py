"""Centralized logging configuration for the Blogger Automation Platform."""

import logging
import sys
from pathlib import Path
from typing import Any

import structlog


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_file_path: Path | None = None,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format - 'json' for production, 'plain' for development
        log_file_path: Optional path to write logs to file

    Design decisions:
        - Uses structlog for structured logging when JSON format is selected
        - Adds file handler if log_file_path is provided
        - Configures standard library logging for compatibility with Google libraries
    """
    # Ensure log level is valid
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure standard library logging first
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    # Add file handler if path provided
    if log_file_path:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file_path, encoding="utf-8"))

    # Basic logging configuration
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=handlers,
    )

    # Configure structlog
    if log_format == "json":
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.dev.ConsoleRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


def get_logger(*args: str, **kwargs: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        *args: Logger name components (will be joined with dots)
        **kwargs: Initial context to bind to the logger

    Returns:
        Configured structlog BoundLogger instance

    Example:
        logger = get_logger("core", "auth")
        logger.info("authenticating user", user_id="123")
    """
    name = ".".join(args) if args else __name__
    logger = structlog.get_logger(name)
    if kwargs:
        logger = logger.bind(**kwargs)
    return logger