from dataclasses import dataclass
from typing import List, Set
from domain.value_objects.problem_id import ProblemId

@dataclass
class Skill:
    skill_id: str
    name: str
    description: str
    prerequisites: List[str]  # Список skill_id
    related_problems: List[ProblemId]  # Список problem_id

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if not self.skill_id or not self.skill_id.strip():
            raise ValueError("Skill ID cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("Skill name cannot be empty")

    def is_prerequisite_satisfied_by(self, user_skills: Set[str]) -> bool:
        """Проверяет, удовлетворены ли все предварительные навыки пользователем."""
        return set(self.prerequisites).issubset(user_skills)
