"""
Module for configuring logging settings.
"""

import logging
from typing import Optional


def setup_logging(level: str = "INFO") -> None:
    """
    Sets up the root logger with a specified level and a predefined format.

    This function configures the root logger. It sets the logging level
    and adds a handler (StreamHandler to stdout) with a specific formatter
    that includes level, logger name, filename, line number, function name,
    and the log message.

    Args:
        level: The logging level as a string. Defaults to "INFO".
               Valid values are "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".

    Returns:
        None
    """
    # Define the log format string
    log_format = "[%(levelname)s] %(name)s [%(filename)s:%(lineno)d - %(funcName)s()] - %(message)s"

    # Parse the string level to a logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure the root logger
    # basicConfig is used here. Note that if this function is called multiple times
    # and handlers already exist, basicConfig might not reconfigure them unless
    # force=True is used (available from Python 3.8+).
    # For simplicity in this implementation, we use basicConfig.
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[logging.StreamHandler()]
    )

