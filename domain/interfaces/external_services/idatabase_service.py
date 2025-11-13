"""
Domain interfaces for database services.

These interfaces define the contracts for data persistence operations,
ensuring that domain logic remains independent of specific database implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from domain.models.problem import Problem
from domain.value_objects.problem_id import ProblemId

class IDatabaseService(ABC):
    """
    Interface for database operations.
    
    Business Rules:
    - Provides persistence for domain entities
    - Handles database connection management
    - Abstracts away database-specific details
    - Ensures data integrity and consistency
    """
    
    @abstractmethod
    async def save_problem(self, problem: Problem) -> bool:
        """
        Save a problem to the database.
        
        Args:
            problem: Domain problem entity to save
            
        Returns:
            True if saved successfully, False otherwise
            
        Business Rules:
        - Must handle duplicate problems gracefully
        - Should update existing problems if they already exist
        - Must maintain data integrity
        """
        pass
    
    @abstractmethod
    async def get_problem_by_id(self, problem_id: ProblemId) -> Optional[Problem]:
        """
        Get problem by ID.
        
        Args:
            problem_id: Problem ID to search for
            
        Returns:
            Problem entity if found, None otherwise
            
        Business Rules:
        - Must handle invalid problem IDs gracefully
        - Should return None if problem doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_problems_by_subject(self, subject: str) -> List[Problem]:
        """
        Get problems by subject.
        
        Args:
            subject: Subject name to filter by
            
        Returns:
            List of problem entities
            
        Business Rules:
        - Must handle invalid subject names gracefully
        - Should return empty list if no problems found
        """
        pass
    
    @abstractmethod
    async def count_problems_by_subject(self, subject: str) -> int:
        """
        Count problems by subject.
        
        Args:
            subject: Subject name to count
            
        Returns:
            Number of problems for the subject
            
        Business Rules:
        - Must return 0 if subject doesn't exist
        - Should be efficient for large datasets
        """
        pass
    
    @abstractmethod
    async def initialize_database(self) -> None:
        """
        Initialize database schema.
        
        Business Rules:
        - Must be idempotent (safe to call multiple times)
        - Should not lose existing data
        - Must handle schema migrations gracefully
        """
        pass
