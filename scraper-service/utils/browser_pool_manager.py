"""Module for managing a pool of BrowserManager instances for parallel scraping."""

import asyncio
import logging
from typing import List
from utils.browser_manager import BrowserManager

logger = logging.getLogger(__name__)


class BrowserPoolManager:
    """Manages a pool of BrowserManager instances for parallel scraping."""

    def __init__(self, pool_size: int = 3):
        """
        Initialize the browser pool.

        Args:
            pool_size: Number of BrowserManager instances to maintain in the pool.
        """
        self.pool_size = pool_size
        self._browsers: List[BrowserManager] = []
        self._queue: asyncio.Queue[BrowserManager] = asyncio.Queue()

    async def __aenter__(self):
        """Initialize the browser pool when entering the context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close all browsers in the pool when exiting the context."""
        await self.close_all()

    async def initialize(self):
        """Initialize all BrowserManager instances and populate the queue."""
        logger.info(f"Initializing BrowserPoolManager with pool size {self.pool_size}")
        for i in range(self.pool_size):
            browser_manager = BrowserManager()
            await browser_manager.__aenter__()  # Initialize the browser
            self._browsers.append(browser_manager)
            await self._queue.put(browser_manager)
        logger.info(f"BrowserPoolManager initialized with {self.pool_size} browsers")

    async def get_available_browser(self) -> BrowserManager:
        """
        Get an available BrowserManager from the pool.

        Returns:
            An available BrowserManager instance.
        """
        logger.debug("Waiting for available browser from pool")
        browser_manager = await self._queue.get()
        logger.info(f"Browser retrieved from pool. Pool usage: {self._queue.qsize()}/{self.pool_size}")
        return browser_manager

    async def return_browser(self, browser_manager: BrowserManager):
        """
        Return a BrowserManager instance back to the pool.

        Args:
            browser_manager: The BrowserManager instance to return.
        """
        logger.debug("Returning browser to pool")
        await self._queue.put(browser_manager)
        logger.info(f"Browser returned to pool. Pool usage: {self._queue.qsize()}/{self.pool_size}")

    async def close_all(self):
        """Close all BrowserManager instances in the pool."""
        logger.info("Closing all browsers in pool")
        while not self._queue.empty():
            try:
                browser_manager = self._queue.get_nowait()
                await browser_manager.__aexit__(None, None, None)
            except asyncio.QueueEmpty:
                break

        for browser_manager in self._browsers:
            if browser_manager._browser is not None:
                await browser_manager.__aexit__(None, None, None)

        self._browsers.clear()
        logger.info("All browsers in pool closed")
        
    async def get_general_page(self):
        """
        Get a general-purpose page from an available browser in the pool.
        This method gets a browser, creates a general page, and returns it.
        The caller is responsible for closing the page and returning the browser.
        """
        logger.debug("Getting general-purpose page from pool")
        browser_manager = await self.get_available_browser()
        try:
            page = await browser_manager.get_general_page()
            # Attach the browser_manager to the page so it can be returned later
            page._browser_manager_for_return = browser_manager
            return page
        except Exception:
            # If getting the page fails, return the browser to the pool
            await self.return_browser(browser_manager)
            raise

    async def _return_page_and_browser(self, page):
        """
        Return a page's browser back to the pool.
        This is a helper method for internal use.
        """
        if hasattr(page, '_browser_manager_for_return'):
            browser_manager = page._browser_manager_for_return
            await page.close()  # Close the page
            await self.return_browser(browser_manager)  # Return the browser to pool
        else:
            logger.warning("Page does not have associated browser manager for return")
            if hasattr(page, 'close'):
                await page.close()

