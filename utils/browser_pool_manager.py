"""Module for managing a pool of BrowserManager instances for parallel scraping with memory cleanup."""
import asyncio
import logging
from typing import List
from utils.browser_manager import BrowserManager

logger = logging.getLogger(__name__)


class BrowserPoolManager:
    """Manages a pool of BrowserManager instances for parallel scraping with memory cleanup."""

    def __init__(self, pool_size: int = 3, max_requests_per_context: int = 50):
        """
        Initialize the browser pool.

        Args:
            pool_size: Number of BrowserManager instances to maintain in the pool.
            max_requests_per_context: Maximum number of requests before context cleanup (default 50).
        """
        self.pool_size = pool_size
        self.max_requests_per_context = max_requests_per_context
        self._browsers: List[BrowserManager] = []
        self._queue: asyncio.Queue[BrowserManager] = asyncio.Queue()
        self._request_counts: dict = {}  # Track requests per browser

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
            self._request_counts[id(browser_manager)] = 0
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
        
        Also checks if cleanup is needed based on request count.

        Args:
            browser_manager: The BrowserManager instance to return.
        """
        logger.debug("Returning browser to pool")
        
        # Increment request count and check if cleanup is needed
        browser_id = id(browser_manager)
        self._request_counts[browser_id] = self._request_counts.get(browser_id, 0) + 1
        
        if self._request_counts[browser_id] >= self.max_requests_per_context:
            logger.info(f"Performing memory cleanup for browser after {self.max_requests_per_context} requests")
            await self._cleanup_browser_context(browser_manager)
            self._request_counts[browser_id] = 0  # Reset counter after cleanup
            
        await self._queue.put(browser_manager)
        logger.info(f"Browser returned to pool. Pool usage: {self._queue.qsize()}/{self.pool_size}")

    async def _cleanup_browser_context(self, browser_manager: BrowserManager):
        """Perform memory cleanup on browser context."""
        logger.debug("Starting browser context cleanup")
        try:
            # Get all pages and clear cookies/reload
            if browser_manager._browser:
                contexts = browser_manager._browser.contexts
                for context in contexts:
                    pages = context.pages
                    for page in pages:
                        try:
                            await page.context.clear_cookies()
                            await page.reload(timeout=5000)
                            logger.debug(f"Cleared cookies and reloaded page: {page.url}")
                        except Exception as e:
                            logger.warning(f"Error during page cleanup: {e}")
                            
            logger.info("Browser context cleanup completed")
        except Exception as e:
            logger.error(f"Error during browser context cleanup: {e}")

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
