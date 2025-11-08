from typing import Optional, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from models.problem_schema import Problem
from abc import ABC, abstractmethod
from typing import Protocol, Optional
import logging
from api.schemas import CheckAnswerResponse


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


class IStorageProvider(Protocol):
    """Interface for local storage operations."""
    def get_answer_and_status(self, problem_id: str):
        ...
    
    def save_answer_and_status(self, problem_id: str, answer: str, status: str):
        ...

class IDatabaseProvider(Protocol):
    """Interface for database operations."""
    
    def get_problem_by_id(self, problem_id: str) -> Optional[Any]:
        """Get problem by its ID."""
        ...
    
    def save_problem(self, problem: object) -> None:
        """Save a problem to the database."""
        ...
    
    def get_answer_status(self, problem_id: str) -> Optional[str]:
        """Get the status of an answer for a problem."""
        ...
    
    def save_answer_status(self, problem_id: str, status: str) -> None:
        """Save the status of an answer for a problem."""
        ...


class IProblemRetriever(Protocol):
    """Interface for problem retrieval operations."""
    
    def retrieve_similar_problems(self, query: str, limit: int = 5) -> List[Any]:
        """Retrieve problems similar to the query."""
        ...
