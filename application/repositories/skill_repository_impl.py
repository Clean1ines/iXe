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
from .base_repository import BaseRepository


class SkillRepositoryImpl(ISkillRepository, BaseRepository):
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
        BaseRepository.__init__(self)
        self._db_adapter = db_adapter

    async def get_by_id(self, skill_id: str) -> Optional[Skill]:
        """
        Retrieve a skill by its ID.

        Args:
            skill_id: The unique identifier of the skill

        Returns:
            The skill domain entity if found, None otherwise
        """
        try:
            db_skill = await self._db_adapter.get_skill_by_id(skill_id)
            if db_skill is None:
                return None
            
            # Use safe attribute access to handle missing fields
            # Remove created_at and updated_at as they don't exist in Skill model
            return Skill(
                skill_id=self._safe_getattr(db_skill, 'skill_id', skill_id),
                name=self._safe_getattr(db_skill, 'name', ''),
                description=self._safe_getattr(db_skill, 'description', ''),
                prerequisites=self._safe_getattr(db_skill, 'prerequisites', []),
                related_problems=[
                    ProblemId(pid) for pid in self._safe_getattr(db_skill, 'related_problems', [])
                ],
            )
        except Exception as e:
            self._handle_conversion_error("skill", e)
            return None

    async def get_all(self) -> List[Skill]:
        """
        Retrieve all skills.

        Returns:
            List of all skill domain entities
        """
        try:
            db_skills = await self._db_adapter.get_all_skills()
            return [self._convert_db_to_skill(db_skill) for db_skill in db_skills]
        except Exception as e:
            self._handle_conversion_error("all skills", e)
            return []

    async def get_by_problem_id(self, problem_id: ProblemId) -> List[Skill]:
        """
        Retrieve all skills associated with a specific problem.

        Args:
            problem_id: The problem identifier

        Returns:
            List of skill domain entities associated with the problem
        """
        try:
            # Convert ProblemId to string for infrastructure layer
            problem_id_str = self._convert_problem_id(problem_id)
            db_skills = await self._db_adapter.get_skills_by_problem_id(problem_id_str)
            return [self._convert_db_to_skill(db_skill) for db_skill in db_skills]
        except Exception as e:
            self._handle_conversion_error("skills by problem ID", e)
            return []

    def _convert_db_to_skill(self, db_skill) -> Skill:
        """
        Convert database skill record to domain skill entity.
        
        Business Rules:
        - Handles missing fields gracefully
        - Provides default values for required fields
        - Preserves backward compatibility
        
        Args:
            db_skill: Database skill record
            
        Returns:
            Domain skill entity
        """
        return Skill(
            skill_id=self._safe_getattr(db_skill, 'skill_id', ''),
            name=self._safe_getattr(db_skill, 'name', ''),
            description=self._safe_getattr(db_skill, 'description', ''),
            prerequisites=self._safe_getattr(db_skill, 'prerequisites', []),
            related_problems=[
                ProblemId(pid) for pid in self._safe_getattr(db_skill, 'related_problems', [])
            ],
        )
