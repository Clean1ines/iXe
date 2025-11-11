from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.models import Problem
from domain.models.answer_schema import AnswerCheckResult, UserAnswer

class ICacheProvider(ABC):
    """Interface for cache operations"""
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        pass

class IExternalChecker(ABC):
    """Interface for external answer checking services"""
    @abstractmethod
    async def check_answer(self, problem_id: str, user_answer: UserAnswer, subject: str) -> AnswerCheckResult:
        pass

class IStorageProvider(ABC):
    """Interface for local storage operations"""
    @abstractmethod
    def get_answer_and_status(self, problem_id: str, user_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def save_answer_and_status(self, problem_id: str, user_id: str, answer: str, is_correct: bool, score: float):
        pass

class IDatabaseProvider(ABC):
    """Interface for database operations"""
    @abstractmethod
    async def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        pass
    
    @abstractmethod
    async def save_problem(self, problem: Problem) -> None:
        pass
    
    @abstractmethod
    async def get_answer_status(self, problem_id: str, user_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    async def save_answer_status(self, problem_id: str, user_id: str, answer: str, is_correct: bool, score: float) -> None:
        pass
    
    # Методы, необходимые для работы endpoint'ов subjects
    @abstractmethod
    def get_all_subjects(self) -> List[str]:
        """Get all available subjects from the database."""
        pass
    
    @abstractmethod
    def get_random_problem_ids(self, subject: str, count: int) -> List[str]:
        """Get random problem IDs for a given subject."""
        pass

class IProblemRetriever(ABC):
    """Interface for problem retrieval operations"""
    @abstractmethod
    async def retrieve_similar_problems(self, query: str, limit: int = 5) -> List[Problem]:
        pass
