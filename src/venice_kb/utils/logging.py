"""Structured logging setup."""

import logging

from rich.logging import RichHandler

from venice_kb.config import LOG_LEVEL


def setup_logging(level: str | None = None) -> logging.Logger:
    """Setup structured logging with rich formatting.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, uses LOG_LEVEL from config

    Returns:
        Configured logger instance
    """
    log_level = level or LOG_LEVEL

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                show_time=True,
                show_path=True,
            )
        ],
    )

    logger = logging.getLogger("venice_kb")
    logger.setLevel(log_level)

    return logger


# Create default logger instance
logger = setup_logging()
