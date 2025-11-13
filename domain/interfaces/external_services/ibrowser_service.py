"""
Domain interfaces for browser-related services.

These interfaces define the contracts that infrastructure adapters must implement,
ensuring proper separation of concerns between domain logic and infrastructure details.
"""
from abc import ABC, abstractmethod
from typing import AsyncContextManager, Any, Optional

class IBrowserService(ABC):
    """
    Interface for browser management services.
    
    Business Rules:
    - Provides browser instances for scraping operations
    - Manages browser lifecycle and resource cleanup
    - Supports concurrent scraping operations
    - Abstracts away implementation details of browser automation
    """
    
    @abstractmethod
    async def get_browser(self) -> Any:
        """
        Get an available browser instance.
        
        Returns:
            Browser instance ready for scraping operations
            
        Business Rules:
        - Must handle browser pooling internally
        - Should block until browser is available if pool is exhausted
        - Must ensure browser is properly initialized
        """
        pass
    
    @abstractmethod
    async def release_browser(self, browser: Any) -> None:
        """
        Release browser back to the pool.
        
        Args:
            browser: Browser instance to release
            
        Business Rules:
        - Must not close the browser, just return it to pool
        - Should handle invalid browser instances gracefully
        - Must be safe to call multiple times
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close all browser resources.
        
        Business Rules:
        - Must close all browsers in the pool
        - Should wait for all operations to complete
        - Must be idempotent (safe to call multiple times)
        """
        pass
    
    @abstractmethod
    async def get_page_content(self, url: str, timeout: int = 30) -> str:
        """
        Get page content from URL.
        
        Args:
            url: URL to fetch
            timeout: Timeout in seconds
            
        Returns:
            HTML content of the page
            
        Business Rules:
        - Must handle network errors gracefully
        - Should respect timeout parameter
        - Must return empty string on failure with proper logging
        """
        pass
