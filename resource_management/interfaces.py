from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

@runtime_checkable
class IBrowserResource(Protocol):
    """Interface for browser resources that require lifecycle management."""
    
    @abstractmethod
    async def initialize(self):
        """Initialize the browser resource."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close and cleanup the browser resource."""
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if the resource is healthy."""
        pass

class IResourcePool(Protocol):
    """Interface for resource pools."""
    
    @abstractmethod
    async def acquire(self):
        """Acquire a resource from the pool."""
        pass
    
    @abstractmethod
    async def release(self, resource):
        """Release a resource back to the pool."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> dict:
        """Get resource pool statistics."""
        pass
