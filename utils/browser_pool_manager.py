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

    async def initialize(self):
        """Initialize all BrowserManager instances and populate the queue."""
        logger.info(f"Initializing BrowserPoolManager with pool size {self.pool_size}")
        for i in range(self.pool_size):
            browser_manager = BrowserManager()
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
        logger.debug("Browser retrieved from pool")
        return browser_manager

    async def return_browser(self, browser_manager: BrowserManager):
        """
        Return a BrowserManager instance back to the pool.

        Args:
            browser_manager: The BrowserManager instance to return.
        """
        logger.debug("Returning browser to pool")
        await self._queue.put(browser_manager)
        logger.debug("Browser returned to pool")

    async def close_all(self):
        """Close all BrowserManager instances in the pool."""
        logger.info("Closing all browsers in pool")
        while not self._queue.empty():
            try:
                browser_manager = self._queue.get_nowait()
                await browser_manager.close()
            except asyncio.QueueEmpty:
                break

        for browser_manager in self._browsers:
            if browser_manager._browser is not None:
                await browser_manager.close()

        self._browsers.clear()
        logger.info("All browsers in pool closed")
