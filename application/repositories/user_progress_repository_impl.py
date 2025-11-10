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
from utils.model_adapter import ModelAdapter


class UserProgressRepositoryImpl(IUserProgressRepository):
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
        self._db_adapter = db_adapter

    async def save(self, progress: UserProgress) -> None:
        """
        Save a user progress domain entity to the database.

        This method converts the domain entity to a database model and
        persists it using the infrastructure adapter.

        Args:
            progress: The user progress domain entity to save
        """
        db_progress = ModelAdapter.domain_to_db_user_progress(progress)
        await self._db_adapter.save_user_progress(db_progress)

    async def get_by_user_and_problem(self, user_id: str, problem_id: ProblemId) -> Optional[UserProgress]:
        """
        Retrieve user progress for a specific problem.

        Args:
            user_id: The user identifier
            problem_id: The problem identifier

        Returns:
            The user progress domain entity if found, None otherwise
        """
        db_progress = await self._db_adapter.get_user_progress_by_user_and_problem(user_id, str(problem_id))
        if db_progress:
            return ModelAdapter.db_to_domain_user_progress(db_progress)
        return None

    async def get_by_user(self, user_id: str) -> List[UserProgress]:
        """
        Retrieve all progress records for a user.

        Args:
            user_id: The user identifier

        Returns:
            List of user progress domain entities for the user
        """
        db_progresses = await self._db_adapter.get_user_progress_by_user(user_id)
        return [ModelAdapter.db_to_domain_user_progress(db_prog) for db_prog in db_progresses]

    async def get_completed_by_user(self, user_id: str) -> List[UserProgress]:
        """
        Retrieve all completed progress records for a user.

        Args:
            user_id: The user identifier

        Returns:
            List of completed user progress domain entities for the user
        """
        db_progresses = await self._db_adapter.get_completed_user_progress_by_user(user_id)
        return [ModelAdapter.db_to_domain_user_progress(db_prog) for db_prog in db_progresses]
