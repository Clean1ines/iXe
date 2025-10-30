"""
Configuration module for the FIPI Parser.

This module loads environment variables from a .env file and provides
centralized access to configuration parameters used throughout the application.
"""

import os
from pathlib import Path

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Existing configuration (keep as is) ---
FIPI_SUBJECTS_URL: str = os.getenv("FIPI_SUBJECTS_URL", "https://ege.fipi.ru/bank/")
FIPI_QUESTIONS_URL: str = os.getenv("FIPI_QUESTIONS_URL", f"{FIPI_SUBJECTS_URL.rstrip('/')}/questions.php")
FIPI_DEFAULT_PROJ_ID: str = os.getenv("FIPI_DEFAULT_PROJ_ID", "AC437B34557F88EA4115D2F374B0A07B")
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID: str = os.getenv("TELEGRAM_USER_ID")
DATA_ROOT: Path = Path(os.getenv("FIPI_DATA_ROOT", Path.home() / "iXe" / "data")).resolve()
OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "problems")).resolve()
TOTAL_PAGES: int = int(os.getenv("TOTAL_PAGES", 98))
BROWSER_USER_AGENT: str = os.getenv(
    "BROWSER_USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
)
BROWSER_HEADLESS: bool = os.getenv("BROWSER_HEADLESS", "True").lower() != "false"

# --- NEW: Environment profile for API behavior ---
ENV: str = os.getenv("ENV", "local")  # local, render, production
USE_LOCAL_STORAGE: bool = os.getenv("USE_LOCAL_STORAGE", "true").lower() == "true"
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
DB_PATH: str = os.getenv("DB_PATH", "data/math/fipi_data.db")

# Helper property (use as `config.is_stateless`)
def is_stateless() -> bool:
    return ENV in ("render", "production")
