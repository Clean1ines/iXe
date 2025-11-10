from abc import abstractmethod
from typing import Protocol, List, Optional
from domain.models.problem import Problem
from domain.models.user_progress import UserProgress, ProgressStatus
from domain.models.skill import Skill
from domain.value_objects.problem_id import ProblemId

class IProblemRepository(Protocol):
    @abstractmethod
    async def save(self, problem: Problem) -> None: ...
    
    @abstractmethod
    async def get_by_id(self, problem_id: ProblemId) -> Optional[Problem]: ...
    
    @abstractmethod
    async def get_by_subject(self, subject: str) -> List[Problem]: ...
    
    @abstractmethod
    async def get_by_exam_part(self, exam_part: str) -> List[Problem]: ...
    
    @abstractmethod
    async def get_by_difficulty(self, difficulty: str) -> List[Problem]: ...

class IUserProgressRepository(Protocol):
    @abstractmethod
    async def save(self, progress: UserProgress) -> None: ...
    
    @abstractmethod
    async def get_by_user_and_problem(self, user_id: str, problem_id: ProblemId) -> Optional[UserProgress]: ...
    
    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[UserProgress]: ...
    
    @abstractmethod
    async def get_completed_by_user(self, user_id: str) -> List[UserProgress]: ...

class ISkillRepository(Protocol):
    @abstractmethod
    async def get_by_id(self, skill_id: str) -> Optional[Skill]: ...
    
    @abstractmethod
    async def get_all(self) -> List[Skill]: ...
    
    @abstractmethod
    async def get_by_problem_id(self, problem_id: ProblemId) -> List[Skill]: ...
