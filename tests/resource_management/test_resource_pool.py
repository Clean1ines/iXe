import pytest
import asyncio
from resource_management.pool import BrowserResourcePool
from resource_management.browser_manager import BrowserManager
from resource_management.circuit_breaker import CircuitBreakerConfig


@pytest.mark.asyncio
async def test_resource_pool_basic_operations():
    """Test basic resource pool operations."""
    async def create_browser():
        return BrowserManager()
    
    pool = BrowserResourcePool(create_browser, max_size=2)
    await pool.initialize()
    
    try:
        # Test resource acquisition
        resource1 = await pool.acquire()
        stats = await pool.get_stats()
        assert stats['acquired_count'] == 1
        assert stats['available_count'] == 1
        
        # Test resource release
        await pool.release(resource1)
        stats = await pool.get_stats()
        assert stats['acquired_count'] == 0
        assert stats['available_count'] == 2
        
    finally:
        await pool.close_all()


@pytest.mark.asyncio
async def test_resource_pool_context_manager():
    """Test resource pool context manager."""
    async def create_browser():
        return BrowserManager()
    
    pool = BrowserResourcePool(create_browser, max_size=1)
    await pool.initialize()
    
    try:
        async with pool.get_resource() as resource:
            stats = await pool.get_stats()
            assert stats['acquired_count'] == 1
            assert stats['available_count'] == 0
            
        # Resource should be automatically released
        stats = await pool.get_stats()
        assert stats['acquired_count'] == 0
        assert stats['available_count'] == 1
        
    finally:
        await pool.close_all()


@pytest.mark.asyncio
async def test_resource_pool_max_size():
    """Test resource pool respects max size."""
    async def create_browser():
        return BrowserManager()
    
    pool = BrowserResourcePool(create_browser, max_size=1)
    await pool.initialize()
    
    try:
        # Acquire first resource
        resource1 = await pool.acquire()
        
        # Try to acquire second resource - should wait
        async def try_acquire_second():
            return await pool.acquire()
        
        task = asyncio.create_task(try_acquire_second())
        
        # Should not complete immediately
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=0.1)
            assert False, "Should not acquire second resource immediately"
        except asyncio.TimeoutError:
            pass  # Expected
            
        # Release first resource
        await pool.release(resource1)
        
        # Now second acquisition should succeed
        resource2 = await asyncio.wait_for(task, timeout=1.0)
        await pool.release(resource2)
        
    finally:
        await pool.close_all()
