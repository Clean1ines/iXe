import asyncio
import logging
from typing import List, Optional, TypeVar, Generic
from contextlib import asynccontextmanager

from .interfaces import IResourcePool, IBrowserResource
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .monitor import ResourceMonitor

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=IBrowserResource)

class BrowserResourcePool(IResourcePool, Generic[T]):  # Fixed MRO order
    """Resource pool with circuit breaker and monitoring."""
    
    def __init__(self, resource_factory, max_size: int = 3, circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        self.resource_factory = resource_factory
        self.max_size = max_size
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        
        self._resources: List[T] = []
        self._available: asyncio.Queue[T] = asyncio.Queue()
        self._acquired: set[T] = set()
        self._circuit_breaker = CircuitBreaker(self.circuit_breaker_config)
        self._monitor = ResourceMonitor()
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the resource pool."""
        async with self._lock:
            if self._initialized:
                return
                
            logger.info(f"Initializing resource pool with {self.max_size} resources")
            
            for i in range(self.max_size):
                resource = await self.resource_factory()
                await resource.initialize()
                self._resources.append(resource)
                self._monitor.register_resource(resource)
                await self._available.put(resource)
                
            self._initialized = True
            logger.info(f"Resource pool initialized with {self.max_size} resources")
            
    async def acquire(self) -> T:
        """Acquire a resource from the pool."""
        return await self._circuit_breaker.call(self._acquire_resource)
        
    async def _acquire_resource(self) -> T:
        """Internal method to acquire a resource."""
        if not self._initialized:
            await self.initialize()
            
        resource = await self._available.get()
        self._acquired.add(resource)
        logger.debug(f"Resource acquired. Pool: {self._available.qsize()}/{self.max_size}")
        return resource
        
    async def release(self, resource: T):
        """Release a resource back to the pool."""
        if resource in self._acquired:
            self._acquired.remove(resource)
            await self._available.put(resource)
            logger.debug(f"Resource released. Pool: {self._available.qsize()}/{self.max_size}")
            
    async def get_stats(self) -> dict:
        """Get resource pool statistics."""
        if not self._initialized:
            await self.initialize()
            
        # Get metrics and convert to serializable format
        current_metrics = self._monitor.get_current_metrics()
        avg_metrics = self._monitor.get_average_metrics()
        
        return {
            'available_count': self._available.qsize(),
            'acquired_count': len(self._acquired),
            'total_count': len(self._resources),
            'max_size': self.max_size,
            'circuit_breaker': self._circuit_breaker.get_state_info(),
            'monitor_metrics': {
                'active_resources': current_metrics.active_resources,
                'total_resources': current_metrics.total_resources,
                'memory_usage_mb': current_metrics.memory_usage_mb,
                'cpu_percent': current_metrics.cpu_percent,
                'active_pages': current_metrics.active_pages,
                'timestamp': current_metrics.timestamp.isoformat()
            },
            'average_metrics': {
                'active_resources': avg_metrics.active_resources,
                'total_resources': avg_metrics.total_resources,
                'memory_usage_mb': avg_metrics.memory_usage_mb,
                'cpu_percent': avg_metrics.cpu_percent,
                'active_pages': avg_metrics.active_pages,
                'timestamp': avg_metrics.timestamp.isoformat()
            }
        }
        
    async def close_all(self):
        """Close all resources in the pool."""
        logger.info("Closing all resources in pool")
        
        for resource in self._resources:
            self._monitor.unregister_resource(resource)
            try:
                await resource.close()
            except Exception as e:
                logger.error(f"Error closing resource: {e}")
                
        self._resources.clear()
        self._acquired.clear()
        while not self._available.empty():
            try:
                self._available.get_nowait()
            except asyncio.QueueEmpty:
                break
                
        self._initialized = False
        logger.info("All resources closed")
        
    @asynccontextmanager
    async def get_resource(self):
        """Context manager for resource acquisition and release."""
        resource = await self.acquire()
        try:
            yield resource
        finally:
            await self.release(resource)
