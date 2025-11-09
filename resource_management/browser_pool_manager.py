"""Module for managing a pool of BrowserManager instances for parallel scraping using resource pool."""

import asyncio
import logging
from .pool import BrowserResourcePool
from .browser_manager import BrowserManager

logger = logging.getLogger(__name__)


class BrowserPoolManager:
    """Manages a pool of BrowserManager instances for parallel scraping using resource pool."""

    def __init__(self, pool_size: int = 3):
        """
        Initialize the browser pool.
        
        Args:
            pool_size: Number of BrowserManager instances to maintain in the pool.
        """
        self.pool_size = pool_size
        self._pool = BrowserResourcePool(
            resource_factory=self._create_browser_manager,
            max_size=pool_size
        )
        self._initialized = False

    async def _create_browser_manager(self):
        """Factory method to create a new BrowserManager instance."""
        return BrowserManager()

    async def initialize(self):
        """Initialize the resource pool."""
        await self._pool.initialize()
        self._initialized = True

    async def get_available_browser(self):
        """
        Get an available BrowserManager from the pool.
        
        Returns:
            An available BrowserManager instance.
        """
        logger.debug("Waiting for available browser from pool")
        browser_manager = await self._pool.acquire()
        stats = await self._pool.get_stats()
        logger.info(f"Browser retrieved from pool. Pool usage: {stats['acquired_count']}/{self.pool_size}")
        return browser_manager

    async def return_browser(self, browser_manager):
        """
        Return a BrowserManager instance back to the pool.
        
        Args:
            browser_manager: The BrowserManager instance to return.
        """
        logger.debug("Returning browser to pool")
        await self._pool.release(browser_manager)
        stats = await self._pool.get_stats()
        logger.info(f"Browser returned to pool. Pool usage: {stats['acquired_count']}/{self.pool_size}")

    async def close_all(self):
        """Close all BrowserManager instances in the pool."""
        logger.info("Closing all browsers in pool")
        await self._pool.close_all()
        self._initialized = False
        logger.info("All browsers in pool closed")

    async def get_stats(self):
        """Get pool statistics."""
        return await self._pool.get_stats()

    @property
    def pool(self):
        """Get access to the underlying resource pool for advanced operations."""
        return self._pool
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not self._initialized:
            await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_all()
