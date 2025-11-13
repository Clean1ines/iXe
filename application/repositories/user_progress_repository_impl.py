"""
Implementation of user progress repository interface using infrastructure adapters.

This repository implementation adapts domain entities to infrastructure
concerns and provides the concrete implementation for IUserProgressRepository
interface defined in the domain layer.
"""
from typing import List, Optional
from domain.interfaces.repositories import IUserProgressRepository
from domain.models.user_progress import UserProgress
from domain.value_objects.problem_id import ProblemId
from infrastructure.adapters.database_adapter import DatabaseAdapter
from .base_repository import BaseRepository
import logging


class UserProgressRepositoryImpl(IUserProgressRepository, BaseRepository):
    """
    Concrete implementation of IUserProgressRepository using database infrastructure.

    This class adapts domain UserProgress entities to database models and provides
    the implementation for user progress persistence operations. It serves as the
    bridge between the application layer and infrastructure layer.
    """
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """
        Initialize the user progress repository implementation.

        Args:
            db_adapter: Infrastructure adapter for database operations
        """
        BaseRepository.__init__(self)
        self._db_adapter = db_adapter

    async def save(self, progress: UserProgress) -> None:
        """
        Save a user progress domain entity to the database.

        Args:
            progress: The user progress domain entity to save
        """
        try:
            await self._db_adapter.save_user_progress(progress)
        except Exception as e:
            self._handle_conversion_error("user progress", e)

    async def get_by_user_and_problem(self, user_id: str, problem_id: ProblemId) -> Optional[UserProgress]:
        """
        Retrieve user progress for a specific problem.

        Args:
            user_id: The user identifier
            problem_id: The problem identifier

        Returns:
            The user progress domain entity if found, None otherwise
        """
        try:
            # Convert ProblemId to string for infrastructure layer
            problem_id_str = self._convert_problem_id(problem_id)
            db_progress = await self._db_adapter.get_user_progress_by_user_and_problem(user_id, problem_id_str)
            
            if db_progress is None:
                return None
            
            # Ensure problem_id is converted back to ProblemId object
            if hasattr(db_progress, 'problem_id') and not isinstance(db_progress.problem_id, ProblemId):
                db_progress.problem_id = ProblemId(db_progress.problem_id)
            
            return db_progress
        except Exception as e:
            self._handle_conversion_error("user progress by user and problem", e)
            return None

    async def get_by_user(self, user_id: str) -> List[UserProgress]:
        """
        Retrieve all progress records for a user.

        Args:
            user_id: The user identifier

        Returns:
            List of user progress domain entities for the user
        """
        try:
            progresses = await self._db_adapter.get_user_progress_by_user(user_id)
            # Ensure all problem_id fields are converted to ProblemId objects
            for progress in progresses:
                if hasattr(progress, 'problem_id') and not isinstance(progress.problem_id, ProblemId):
                    progress.problem_id = ProblemId(progress.problem_id)
            return progresses
        except Exception as e:
            self._handle_conversion_error("user progress by user", e)
            return []

    async def get_completed_by_user(self, user_id: str) -> List[UserProgress]:
        """
        Retrieve all completed progress records for a user.

        Args:
            user_id: The user identifier

        Returns:
            List of completed user progress domain entities for the user
        """
        try:
            progresses = await self._db_adapter.get_completed_user_progress_by_user(user_id)
            # Ensure all problem_id fields are converted to ProblemId objects
            for progress in progresses:
                if hasattr(progress, 'problem_id') and not isinstance(progress.problem_id, ProblemId):
                    progress.problem_id = ProblemId(progress.problem_id)
            return progresses
        except Exception as e:
            self._handle_conversion_error("completed user progress", e)
            return []
