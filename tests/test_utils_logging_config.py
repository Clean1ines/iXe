"""
Tests for the logging configuration utility.
"""
import unittest
import logging
from utils.logging_config import configure_logging


class TestLoggingConfig(unittest.TestCase):
    """
    Test suite for the setup_logging function.
    """

    def setUp(self):
        """Reset the root logger's handlers and level before each test."""
        # Get the root logger
        root_logger = logging.getLogger()
        # Remove all existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        # Set the level back to NOTSET
        root_logger.setLevel(logging.NOTSET)

    def test_setup_logging_info_level(self):
        """
        Test that setup_logging correctly sets the root logger level to INFO.
        """
        setup_logging("INFO")
        effective_level = logging.getLogger().getEffectiveLevel()
        self.assertEqual(effective_level, logging.INFO)

    def test_setup_logging_debug_level(self):
        """
        Test that setup_logging correctly sets the root logger level to DEBUG.
        """
        setup_logging("DEBUG")
        effective_level = logging.getLogger().getEffectiveLevel()
        self.assertEqual(effective_level, logging.DEBUG)

    def test_setup_logging_default_level(self):
        """
        Test that setup_logging sets the default level to INFO when no argument is passed.
        """
        setup_logging()  # No argument, should default to "INFO"
        effective_level = logging.getLogger().getEffectiveLevel()
        self.assertEqual(effective_level, logging.INFO)

    def test_setup_logging_invalid_level_defaults_to_info(self):
        """
        Test that setup_logging defaults to INFO level if an invalid level string is passed.
        """
        setup_logging("INVALID_LEVEL")
        effective_level = logging.getLogger().getEffectiveLevel()
        # The implementation defaults to logging.INFO for invalid levels
        self.assertEqual(effective_level, logging.INFO)
