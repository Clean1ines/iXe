"""Module for centralized Playwright browser management."""

import logging
from typing import Dict
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Page, Browser
from utils.answer_checker import FIPIAnswerChecker

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages a single browser instance and caches pages per subject."""

    def __init__(self, base_url: str = "https://ege.fipi.ru"):
        self.base_url = base_url.rstrip("/")
        self._browser: Browser | None = None
        self._pages: Dict[str, Page] = {}
        self._playwright_ctx = None

    async def __aenter__(self):
        """Initialize the browser context."""
        logger.info("Initializing BrowserManager and launching browser.")
        self._playwright_ctx = await async_playwright().start()
        self._browser = await self._playwright_ctx.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the browser and stop Playwright."""
        await self.close()

    async def close(self):
        """Close all cached pages and the browser."""
        logger.info("Closing BrowserManager and all pages.")
        for subject, page in self._pages.items():
            try:
                await page.close()
            except Exception as e:
                logger.warning(f"Error closing page for subject '{subject}': {e}")
        self._pages.clear()

        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            self._browser = None

        if self._playwright_ctx:
            try:
                await self._playwright_ctx.stop()
            except Exception as e:
                logger.error(f"Error stopping Playwright: {e}")
            self._playwright_ctx = None

    async def get_page(self, subject: str) -> Page:
        """
        Get a cached page for a subject or create a new one.

        Args:
            subject: The subject name (e.g., 'math', 'informatics').

        Returns:
            A Playwright Page instance configured for the subject's proj_id.
        """
        if subject in self._pages:
            logger.debug(f"Reusing cached page for subject '{subject}'.")
            return self._pages[subject]

        logger.info(f"Creating new page for subject '{subject}'.")
        if not self._browser:
            raise RuntimeError("Browser is not initialized. Use BrowserManager as an async context manager.")

        page = await self._browser.new_page()
        page.set_default_timeout(30000)  # 30 seconds

        proj_id = FIPIAnswerChecker.get_proj_id_by_subject(subject)
        main_url = f"{self.base_url}/bank/index.php?proj={proj_id}"

        logger.debug(f"Navigating page for '{subject}' to {main_url}")
        await page.goto(main_url, wait_until="networkidle", timeout=30000)

        self._pages[subject] = page
        logger.debug(f"Page for subject '{subject}' created and cached.")
        return page

