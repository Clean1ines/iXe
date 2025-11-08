from abc import ABC, abstractmethod
from typing import Protocol
import logging
from infrastructure.adapters.database_adapter import DatabaseAdapter


class ICacheProvider(Protocol):
    """Interface for cache operations."""
    async def get(self, key: str):
        ...
    
    async def set(self, key: str, value, ttl: int = None):
        ...
    
    async def delete(self, key: str):
        ...


class IExternalChecker(Protocol):
    """Interface for external answer checking services."""
    async def check_answer(self, task_id: str, form_id: str, user_answer: str, subject: str) -> dict:
        ...


class BaseService(ABC):
    """Base service class providing common initialization and logging."""
    
    def __init__(self, db: DatabaseAdapter):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def initialize(self):
        """Initialize service-specific resources."""
        pass
