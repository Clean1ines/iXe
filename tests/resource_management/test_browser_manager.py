import pytest
from resource_management.browser_manager import BrowserManager


@pytest.mark.asyncio
async def test_browser_manager_lifecycle():
    """Test BrowserManager lifecycle methods."""
    manager = BrowserManager()
    
    # Should not be healthy initially
    assert not await manager.is_healthy()
    
    # Initialize
    await manager.initialize()
    assert manager._initialized
    
    # Should be healthy after initialization
    assert await manager.is_healthy()
    
    # Close
    await manager.close()
    assert not manager._initialized
    assert not await manager.is_healthy()


@pytest.mark.asyncio
async def test_browser_manager_interface():
    """Test BrowserManager implements IBrowserResource interface."""
    manager = BrowserManager()
    
    # Check that required methods exist
    assert hasattr(manager, 'initialize')
    assert hasattr(manager, 'close')
    assert hasattr(manager, 'is_healthy')
    
    # Check that they are callable
    assert callable(getattr(manager, 'initialize'))
    assert callable(getattr(manager, 'close'))
    assert callable(getattr(manager, 'is_healthy'))
