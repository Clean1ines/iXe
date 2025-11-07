"""Configuration for structured logging using structlog."""

import logging
import sys
import structlog
from typing import Any, Dict


def configure_logging(level: str = "INFO") -> None:
    """
    Configure structlog with a predefined format and processors for production.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Configure structlog for production (JSON output with exception formatting)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,  # Format exceptions
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),  # Output as JSON
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def configure_logging_dev() -> None:
    """
    Configure structlog with console output format for development.
    """
    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog for development (console output, no complex exception formatting for console)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            # Убираем format_exc_info и используем ConsoleRenderer для разработки
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=False)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured structlog logger instance.

    Args:
        name: Name of the logger (typically __name__ of the module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def add_trace_id(trace_id: str) -> None:
    """
    Add trace ID to the current logging context.

    Args:
        trace_id: Unique trace identifier
    """
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def clear_trace_id() -> None:
    """Clear the current logging context."""
    structlog.contextvars.clear_contextvars()
