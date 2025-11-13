"""
Implementation of problem repository interface using infrastructure adapters.

This repository implementation adapts domain entities to infrastructure
concerns and provides the concrete implementation for IProblemRepository
interface defined in the domain layer.
"""
from typing import List, Optional
from domain.interfaces.repositories import IProblemRepository
from domain.models.problem import Problem
from domain.value_objects.problem_id import ProblemId
from infrastructure.adapters.database_adapter import DatabaseAdapter
from .base_repository import BaseRepository


class ProblemRepositoryImpl(IProblemRepository, BaseRepository):
    """
    Concrete implementation of IProblemRepository using database infrastructure.

    This class adapts domain Problem entities to database models and provides
    the implementation for problem persistence operations. It serves as the
    bridge between the application layer and infrastructure layer.
    
    Business Rules:
    - Inherits from BaseRepository for common functionality
    - Handles proper conversion of Value Objects to primitive types
    - Provides standardized error handling and logging
    - Maintains backward compatibility with original interface
    """
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """
        Initialize the problem repository implementation.

        Args:
            db_adapter: Infrastructure adapter for database operations
        """
        BaseRepository.__init__(self)
        self._db_adapter = db_adapter

    async def save(self, problem: Problem) -> None:
        """
        Save a problem domain entity to the database.

        Args:
            problem: The problem domain entity to save
            
        Business Rules:
        - Standardized error handling
        - Preserves original behavior for backward compatibility
        """
        try:
            await self._db_adapter.save(problem)
        except Exception as e:
            self._handle_conversion_error("problem", e)

    async def get_by_id(self, problem_id: ProblemId) -> Optional[Problem]:
        """
        Retrieve a problem by its ID.

        Args:
            problem_id: The unique identifier of the problem

        Returns:
            The problem domain entity if found, None otherwise
            
        Business Rules:
        - Converts ProblemId Value Object to string for infrastructure layer
        - Handles missing problems gracefully
        - Standardized error logging
        """
        try:
            # Convert ProblemId to string for infrastructure layer
            problem_id_str = self._convert_problem_id(problem_id)
            return await self._db_adapter.get_by_id(problem_id_str)
        except Exception as e:
            self._handle_conversion_error("problem by ID", e)
            return None

    async def get_by_subject(self, subject: str) -> List[Problem]:
        """
        Retrieve all problems for a given subject.

        Args:
            subject: The subject area to filter problems

        Returns:
            List of problem domain entities matching the subject
            
        Business Rules:
        - Standardized error handling
        - Returns empty list on error for backward compatibility
        """
        try:
            return await self._db_adapter.get_by_subject(subject)
        except Exception as e:
            self._handle_conversion_error("problems by subject", e)
            return []

    async def get_by_exam_part(self, exam_part: str) -> List[Problem]:
        """
        Retrieve all problems for a given exam part.

        Args:
            exam_part: The exam part to filter problems (e.g., "Part 1", "Part 2")

        Returns:
            List of problem domain entities matching the exam part
            
        Business Rules:
        - Standardized error handling
        - Returns empty list on error for backward compatibility
        """
        try:
            return await self._db_adapter.get_by_exam_part(exam_part)
        except Exception as e:
            self._handle_conversion_error("problems by exam part", e)
            return []

    async def get_by_difficulty(self, difficulty: str) -> List[Problem]:
        """
        Retrieve all problems for a given difficulty level.

        Args:
            difficulty: The difficulty level to filter problems

        Returns:
            List of problem domain entities matching the difficulty level
            
        Business Rules:
        - Standardized error handling
        - Returns empty list on error for backward compatibility
        """
        try:
            return await self._db_adapter.get_by_difficulty(difficulty)
        except Exception as e:
            self._handle_conversion_error("problems by difficulty", e)
            return []
