# config.py
"""
Configuration module for the FIPI Parser.

This module loads environment variables from a .env file and provides
centralized access to configuration parameters used throughout the application.
"""

import os
from pathlib import Path

# Attempt to load environment variables from a .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, the script will rely on system environment variables
    pass
    # Optionally print a warning
    # print("Warning: python-dotenv not found. Using system environment variables.")

# --- Configuration Variables ---
# Load from environment variables, with sensible defaults if not present

# FIPI Website Configuration
# ИСПРАВЛЕНО: Добавлена отдельная переменная для URL списка предметов
FIPI_SUBJECTS_URL: str = os.getenv("FIPI_SUBJECTS_URL", "https://ege.fipi.ru/bank/")
"""The URL for the FIPI subjects listing page (e.g., the main bank page)."""

# ИСПРАВЛЕНО: Переменная для URL страницы с вопросами
FIPI_QUESTIONS_URL: str = os.getenv("FIPI_QUESTIONS_URL", f"{FIPI_SUBJECTS_URL.rstrip('/')}/questions.php")
"""The base URL for the FIPI questions endpoint."""

FIPI_DEFAULT_PROJ_ID: str = os.getenv("FIPI_DEFAULT_PROJ_ID", "AC437B34557F88EA4115D2F374B0A07B")
"""Default project ID, e.g., for Math Prof. (fallback if needed)."""

# Telegram Configuration (if needed for notifications)
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
"""Telegram Bot Token for sending notifications (optional)."""

TELEGRAM_USER_ID: str = os.getenv("TELEGRAM_USER_ID")
"""Telegram User ID for sending notifications (optional)."""

# Output and Processing Configuration
DATA_ROOT: Path = Path(os.getenv("FIPI_DATA_ROOT", Path.home() / "iXe" / "data")).resolve()
"""Root directory for saving scraped data."""

OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "problems")).resolve()
"""Subdirectory within DATA_ROOT for saving runs (e.g., 'data/problems')."""

TOTAL_PAGES: int = int(os.getenv("TOTAL_PAGES", 98))
"""Total number of pages to scrape per subject."""

# Browser Configuration (Playwright)
BROWSER_USER_AGENT: str = os.getenv(
    "BROWSER_USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
)
"""User agent string to use for the browser session."""

BROWSER_HEADLESS: bool = os.getenv("BROWSER_HEADLESS", "True").lower() != "false"
"""Whether to run the browser in headless mode."""
