"""
Application layer repository interfaces and implementations.

This module provides repository implementations that adapt domain interfaces
to infrastructure concerns, serving as the bridge between application services
and infrastructure adapters.

According to Clean Architecture principles, repositories are implemented in the
application layer as concrete implementations of domain interfaces. This allows
the domain layer to remain independent of infrastructure concerns while providing
the necessary persistence mechanisms.
"""
from .problem_repository_impl import ProblemRepositoryImpl
from .user_progress_repository_impl import UserProgressRepositoryImpl
from .skill_repository_impl import SkillRepositoryImpl

__all__ = [
    "ProblemRepositoryImpl",
    "UserProgressRepositoryImpl", 
    "SkillRepositoryImpl"
]
