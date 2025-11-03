"""Tests for BrowserPoolManager."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from utils.browser_pool_manager import BrowserPoolManager


@pytest.mark.asyncio
async def test_browser_pool_manager_initialization():
    """Test that BrowserPoolManager initializes the correct number of browsers."""
    pool_size = 2
    pool_manager = BrowserPoolManager(pool_size=pool_size)
    
    await pool_manager.initialize()
    
    assert len(pool_manager._browsers) == pool_size
    assert pool_manager._queue.qsize() == pool_size


@pytest.mark.asyncio
async def test_get_and_return_browser():
    """Test getting and returning a browser from the pool."""
    pool_manager = BrowserPoolManager(pool_size=1)
    await pool_manager.initialize()
    
    initial_size = pool_manager._queue.qsize()
    browser = await pool_manager.get_available_browser()
    assert pool_manager._queue.qsize() == initial_size - 1
    
    await pool_manager.return_browser(browser)
    assert pool_manager._queue.qsize() == initial_size


@pytest.mark.asyncio
async def test_concurrent_access():
    """Test that multiple coroutines can access the pool concurrently."""
    pool_manager = BrowserPoolManager(pool_size=2)
    await pool_manager.initialize()
    
    initial_size = pool_manager._queue.qsize()
    
    async def get_and_return():
        browser = await pool_manager.get_available_browser()
        await asyncio.sleep(0.1)  # Simulate some work
        await pool_manager.return_browser(browser)
    
    # Run multiple coroutines concurrently
    await asyncio.gather(*[get_and_return() for _ in range(4)])
    
    # Queue should have same size as initial after all operations
    assert pool_manager._queue.qsize() == initial_size


@pytest.mark.asyncio
async def test_close_all():
    """Test that close_all properly closes all browsers."""
    pool_manager = BrowserPoolManager(pool_size=2)
    await pool_manager.initialize()
    
    # Mock the close method of BrowserManager instances
    for browser in pool_manager._browsers:
        browser.close = AsyncMock()
    
    await pool_manager.close_all()
    
    for browser in pool_manager._browsers:
        browser.close.assert_called_once()
    
    assert len(pool_manager._browsers) == 0
    assert pool_manager._queue.qsize() == 0


@pytest.mark.asyncio
async def test_get_available_blocks_when_empty():
    """Test that get_available_browser blocks when no browsers are available."""
    pool_manager = BrowserPoolManager(pool_size=1)
    await pool_manager.initialize()
    
    # Get the only available browser
    browser = await pool_manager.get_available_browser()
    assert pool_manager._queue.qsize() == 0
    
    # Try to get another browser - should block
    async def try_get_browser():
        return await pool_manager.get_available_browser()
    
    task = asyncio.create_task(try_get_browser())
    await asyncio.sleep(0.1)  # Allow some time for the task to attempt getting browser
    assert not task.done()  # Task should still be waiting
    
    # Return the browser to unblock the task
    await pool_manager.return_browser(browser)
    retrieved_browser = await asyncio.wait_for(task, timeout=1.0)
    assert retrieved_browser is browser
