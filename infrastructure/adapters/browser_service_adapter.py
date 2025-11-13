"""
Infrastructure adapter for browser management.

This adapter implements the IBrowserService interface using Playwright,
providing browser automation capabilities for scraping operations.
"""
import logging
import asyncio
from typing import Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from domain.interfaces.external_services import IBrowserService

logger = logging.getLogger(__name__)

class BrowserServiceAdapter(IBrowserService):
    """
    Adapter for browser management using Playwright.
    
    Business Rules:
    - Manages browser lifecycle properly
    - Supports browser pooling for concurrent operations
    - Handles timeouts and errors gracefully
    - Provides clean HTML content extraction
    """
    
    def __init__(
        self,
        max_browsers: int = 3,
        headless: bool = True,
        timeout_seconds: int = 30,
        user_agent: Optional[str] = None
    ):
        """
        Initialize browser service adapter.
        
        Args:
            max_browsers: Maximum number of browsers in pool
            headless: Whether to run browsers in headless mode
            timeout_seconds: Default timeout for operations
            user_agent: Custom user agent string
        """
        self.max_browsers = max_browsers
        self.headless = headless
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self._browsers: list[Browser] = []
        self._browser_contexts: dict[Browser, BrowserContext] = {}
        self._lock = asyncio.Lock()
        self._playwright = None
        self._is_initialized = False
    
    async def _initialize(self) -> None:
        """Initialize Playwright and browser pool."""
        if self._is_initialized:
            return
        
        async with self._lock:
            if self._is_initialized:
                return
            
            self._playwright = await async_playwright().start()
            
            # Create browser pool
            for _ in range(self.max_browsers):
                browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    timeout=self.timeout_seconds * 1000
                )
                self._browsers.append(browser)
            
            self._is_initialized = True
            logger.info(f"Initialized browser pool with {self.max_browsers} browsers")
    
    async def get_browser(self) -> Any:
        """Get an available browser instance."""
        await self._initialize()
        
        async with self._lock:
            if not self._browsers:
                logger.warning("No available browsers in pool, creating new one")
                return await self._create_new_browser()
            
            browser = self._browsers.pop(0)
            return browser
    
    async def release_browser(self, browser: Any) -> None:
        """Release browser back to the pool."""
        if not isinstance(browser, Browser):
            logger.warning("Attempted to release invalid browser instance")
            return
        
        async with self._lock:
            if browser in self._browsers:
                logger.warning("Browser already in pool, skipping release")
                return
            
            if browser.is_connected():
                self._browsers.append(browser)
            else:
                logger.warning("Browser is not connected, creating new one")
                new_browser = await self._create_new_browser()
                self._browsers.append(new_browser)
    
    async def close(self) -> None:
        """Close all browser resources."""
        async with self._lock:
            if not self._is_initialized:
                return
            
            for browser in self._browsers:
                try:
                    await browser.close()
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
            
            self._browsers = []
            
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception as e:
                    logger.warning(f"Error stopping playwright: {e}")
            
            self._is_initialized = False
            logger.info("Closed all browser resources")
    
    async def get_page_content(self, url: str, timeout: Optional[int] = None) -> str:
        """Get page content from URL."""
        timeout = timeout or self.timeout_seconds
        
        browser = await self.get_browser()
        try:
            page = await browser.new_page()
            if self.user_agent:
                await page.set_extra_http_headers({"User-Agent": self.user_agent})
            
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            content = await page.content()
            return content
        finally:
            await self.release_browser(browser)
    
    async def _create_new_browser(self) -> Browser:
        """Create a new browser instance."""
        if not self._playwright:
            await self._initialize()
        
        return await self._playwright.chromium.launch(
            headless=self.headless,
            timeout=self.timeout_seconds * 1000
        )
    
    async def __aenter__(self) -> "BrowserServiceAdapter":
        """Async context manager entry."""
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
