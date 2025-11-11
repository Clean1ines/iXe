"""Application configuration settings."""

import os
from utils.fipi_urls import FIPI_QUESTIONS_URL, FIPI_SUBJECTS_LIST_URL

# --- Database ---
DB_PATH: str = os.getenv("DB_PATH", "data/tasks.db")

# --- Storage ---
USE_LOCAL_STORAGE: bool = os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"

# --- FIPI URLs ---
# These are now imported from the centralized URLs module.
# Config provides a single point of access, potentially allowing overrides via env vars in the future.
# Currently, they directly reference the constants from fipi_urls.
FIPI_QUESTIONS_URL: str = os.getenv("FIPI_QUESTIONS_URL", FIPI_QUESTIONS_URL)
FIPI_SUBJECTS_URL: str = os.getenv("FIPI_SUBJECTS_URL", FIPI_SUBJECTS_LIST_URL) # Use the correct subjects list URL

# --- Qdrant ---
QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))

# --- Application ---
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
BROWSER_HEADLESS = True
TOTAL_PAGES = 10
FIPI_DEFAULT_PROJ_ID = 'MATH_PROFILE'
FRONTEND_URL = 'http://localhost:5173/'