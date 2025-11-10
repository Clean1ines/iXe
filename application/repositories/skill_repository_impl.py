"""
Implementation of skill repository interface using infrastructure adapters.

This repository implementation adapts domain entities to infrastructure
concerns and provides the concrete implementation for ISkillRepository
interface defined in the domain layer.
"""
from typing import List, Optional
from domain.interfaces.repositories import ISkillRepository
from domain.models.skill import Skill
from domain.value_objects.problem_id import ProblemId
from infrastructure.adapters.database_adapter import DatabaseAdapter
from utils.model_adapter import (
    domain_to_db_problem, db_to_domain_problem,
    domain_to_db_user_progress, db_to_domain_user_progress,
    domain_to_db_skill, db_to_domain_skill
)


class SkillRepositoryImpl(ISkillRepository):
    """
    Concrete implementation of ISkillRepository using database infrastructure.

    This class adapts domain Skill entities to database models and provides
    the implementation for skill persistence operations. It serves as the
    bridge between the application layer and infrastructure layer.
    """
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """
        Initialize the skill repository implementation.

        Args:
            db_adapter: Infrastructure adapter for database operations
        """
        self._db_adapter = db_adapter

    async def get_by_id(self, skill_id: str) -> Optional[Skill]:
        """
        Retrieve a skill by its ID.

        Args:
            skill_id: The unique identifier of the skill

        Returns:
            The skill domain entity if found, None otherwise
        """
        return await self._db_adapter.get_skill_by_id(skill_id)

    async def get_all(self) -> List[Skill]:
        """
        Retrieve all skills.

        Returns:
            List of all skill domain entities
        """
        return await self._db_adapter.get_all_skills()

    async def get_by_problem_id(self, problem_id: ProblemId) -> List[Skill]:
        """
        Retrieve all skills associated with a specific problem.

        Args:
            problem_id: The problem identifier

        Returns:
            List of skill domain entities associated with the problem
        """
        return await self._db_adapter.get_skills_by_problem_id(str(problem_id))
