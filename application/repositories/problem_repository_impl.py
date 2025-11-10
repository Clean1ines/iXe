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
from utils.model_adapter import ModelAdapter


class ProblemRepositoryImpl(IProblemRepository):
    """
    Concrete implementation of IProblemRepository using database infrastructure.

    This class adapts domain Problem entities to database models and provides
    the implementation for problem persistence operations. It serves as the
    bridge between the application layer and infrastructure layer.
    """
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """
        Initialize the problem repository implementation.

        Args:
            db_adapter: Infrastructure adapter for database operations
        """
        self._db_adapter = db_adapter

    async def save(self, problem: Problem) -> None:
        """
        Save a problem domain entity to the database.

        This method converts the domain entity to a database model and
        persists it using the infrastructure adapter.

        Args:
            problem: The problem domain entity to save
        """
        db_problem = ModelAdapter.domain_to_db_problem(problem)
        await self._db_adapter.save_problem(db_problem)

    async def get_by_id(self, problem_id: ProblemId) -> Optional[Problem]:
        """
        Retrieve a problem by its ID.

        Args:
            problem_id: The unique identifier of the problem

        Returns:
            The problem domain entity if found, None otherwise
        """
        db_problem = await self._db_adapter.get_problem_by_id(str(problem_id))
        if db_problem:
            return ModelAdapter.db_to_domain_problem(db_problem)
        return None

    async def get_by_subject(self, subject: str) -> List[Problem]:
        """
        Retrieve all problems for a given subject.

        Args:
            subject: The subject area to filter problems

        Returns:
            List of problem domain entities matching the subject
        """
        db_problems = await self._db_adapter.get_problems_by_subject(subject)
        return [ModelAdapter.db_to_domain_problem(db_prob) for db_prob in db_problems]

    async def get_by_exam_part(self, exam_part: str) -> List[Problem]:
        """
        Retrieve all problems for a given exam part.

        Args:
            exam_part: The exam part to filter problems (e.g., "Part 1", "Part 2")

        Returns:
            List of problem domain entities matching the exam part
        """
        db_problems = await self._db_adapter.get_problems_by_exam_part(exam_part)
        return [ModelAdapter.db_to_domain_problem(db_prob) for db_prob in db_problems]

    async def get_by_difficulty(self, difficulty: str) -> List[Problem]:
        """
        Retrieve all problems for a given difficulty level.

        Args:
            difficulty: The difficulty level to filter problems

        Returns:
            List of problem domain entities matching the difficulty level
        """
        db_problems = await self._db_adapter.get_problems_by_difficulty(difficulty)
        return [ModelAdapter.db_to_domain_problem(db_prob) for db_prob in db_problems]
