"""
Infrastructure adapter for managing SQLite connections and performing CRUD operations
on tasks, answers, and user progress using SQLAlchemy ORM.

This adapter implements the domain repository interfaces and serves as the
bridge between application services and the database infrastructure.
"""
import datetime
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from domain.models.database_models import Base, DBProblem, DBAnswer, DBUserProgress, DBSkill
from domain.interfaces.repositories import IProblemRepository, IUserProgressRepository, ISkillRepository
from domain.models.problem import Problem as DomainProblem
from domain.models.user_progress import UserProgress as DomainUserProgress
from domain.models.skill import Skill as DomainSkill
from domain.value_objects.problem_id import ProblemId
from utils.model_adapter import (
    domain_to_db_problem, db_to_domain_problem,
    domain_to_db_user_progress, db_to_domain_user_progress,
    domain_to_db_skill, db_to_domain_skill
)
from domain.interfaces.infrastructure_adapters import IDatabaseProvider


logger = logging.getLogger(__name__)


class DatabaseAdapter(IDatabaseProvider):
    """
    Infrastructure adapter implementing repository interfaces for database operations.

    This class implements the domain repository interfaces using SQLAlchemy ORM
    to provide persistence for domain entities. It serves as the concrete
    implementation of the repository pattern in the infrastructure layer.
    """

    def __init__(self, db_path: str = "data/fipi_data.db"):
        self.db_path = db_path
        self.engine = sa.create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        # Для асинхронных операций - создаем асинхронный движок только при необходимости
        try:
            self.async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        except:
            # В тестах может не быть aiosqlite
            self.async_engine = None
        self._ensure_tables()

    def _ensure_tables(self):
        """Create tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def async_session(self):
        """Provide async session context manager."""
        if self.async_engine is None:
            raise RuntimeError("Async engine not available. Install aiosqlite.")
        return AsyncSession(self.async_engine)

    # IProblemRepository implementation
    async def save(self, problem: DomainProblem) -> None:
        """Save a domain problem entity to the database."""
        db_problem = domain_to_db_problem(problem)
        
        with self.SessionLocal() as session:
            # Check if problem already exists
            existing = session.query(DBProblem).filter(DBProblem.problem_id == problem.problem_id.value).first()
            if existing:
                # Update existing problem
                for field in ['subject', 'type', 'text', 'answer', 'options', 'solutions',
                              'topics', 'difficulty_level', 'task_number',
                              'kes_codes', 'kos_codes', 'exam_part', 'max_score', 'form_id', 'source_url',
                              'raw_html_path', 'updated_at', 'metadata_']:
                    setattr(existing, field, getattr(db_problem, field))
            else:
                # Add new problem
                session.add(db_problem)
            session.commit()

    async def get_by_id(self, problem_id: ProblemId) -> Optional[DomainProblem]:
        """Retrieve a problem by its ID."""
        with self.SessionLocal() as session:
            db_problem = session.query(DBProblem).filter(DBProblem.problem_id == str(problem_id)).first()
            if db_problem:
                return db_to_domain_problem(db_problem)
        return None

    async def get_by_subject(self, subject: str) -> List[DomainProblem]:
        """Retrieve all problems for a given subject."""
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.subject == subject).all()
            return [db_to_domain_problem(db) for db in db_problems]

    async def get_by_exam_part(self, exam_part: str) -> List[DomainProblem]:
        """Retrieve all problems for a given exam part."""
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.exam_part == exam_part).all()
            return [db_to_domain_problem(db) for db in db_problems]

    async def get_by_difficulty(self, difficulty: str) -> List[DomainProblem]:
        """Retrieve all problems for a given difficulty level."""
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.difficulty_level == difficulty).all()
            return [db_to_domain_problem(db) for db in db_problems]

    # IUserProgressRepository implementation
    async def save_user_progress(self, progress: DomainUserProgress) -> None:
        """Save a domain user progress entity to the database."""
        db_progress = domain_to_db_user_progress(progress)
        
        with self.SessionLocal() as session:
            # Check if progress already exists
            existing = session.query(DBUserProgress).filter(
                DBUserProgress.user_id == progress.user_id,
                DBUserProgress.problem_id == str(progress.problem_id)
            ).first()
            
            if existing:
                # Update existing progress
                for field in ['status', 'score', 'attempts', 'last_attempt_at', 'started_at']:
                    setattr(existing, field, getattr(db_progress, field))
            else:
                # Add new progress
                session.add(db_progress)
            session.commit()

    async def get_user_progress_by_user_and_problem(self, user_id: str, problem_id: str) -> Optional[DomainUserProgress]:
        """Retrieve user progress for a specific problem."""
        with self.SessionLocal() as session:
            db_progress = session.query(DBUserProgress).filter(
                DBUserProgress.user_id == user_id,
                DBUserProgress.problem_id == problem_id
            ).first()
            if db_progress:
                return db_to_domain_user_progress(db_progress)
        return None

    async def get_user_progress_by_user(self, user_id: str) -> List[DomainUserProgress]:
        """Retrieve all progress records for a user."""
        with self.SessionLocal() as session:
            db_progresses = session.query(DBUserProgress).filter(DBUserProgress.user_id == user_id).all()
            return [db_to_domain_user_progress(db) for db in db_progresses]

    async def get_completed_user_progress_by_user(self, user_id: str) -> List[DomainUserProgress]:
        """Retrieve all completed progress records for a user."""
        with self.SessionLocal() as session:
            db_progresses = session.query(DBUserProgress).filter(
                DBUserProgress.user_id == user_id,
                DBUserProgress.status == 'COMPLETED'
            ).all()
            return [db_to_domain_user_progress(db) for db in db_progresses]

    # ISkillRepository implementation
    async def get_skill_by_id(self, skill_id: str) -> Optional[DomainSkill]:
        """Retrieve a skill by its ID."""
        with self.SessionLocal() as session:
            db_skill = session.query(DBSkill).filter(DBSkill.skill_id == skill_id).first()
            if db_skill:
                return db_to_domain_skill(db_skill)
        return None

    async def get_all_skills(self) -> List[DomainSkill]:
        """Retrieve all skills."""
        with self.SessionLocal() as session:
            db_skills = session.query(DBSkill).all()
            return [db_to_domain_skill(db_skill) for db_skill in db_skills]

    async def get_skills_by_problem_id(self, problem_id: str) -> List[DomainSkill]:
        """Retrieve all skills associated with a specific problem."""
        with self.SessionLocal() as session:
            db_skills = session.query(DBSkill).filter(
                DBSkill.related_problems.contains(problem_id)
            ).all()
            return [db_to_domain_skill(db_skill) for db_skill in db_skills]

    # IDatabaseProvider implementation - добавляем недостающий метод
    async def save_answer_status(self, problem_id: str, user_id: str, answer: str, is_correct: bool, score: float) -> None:
        """Save answer status for a user and problem."""
        with self.SessionLocal() as session:
            # Check if answer already exists for this user and problem
            existing_answer = (
                session.query(DBAnswer)
                .filter(DBAnswer.problem_id == problem_id, DBAnswer.user_id == user_id)
                .first()
            )

            if existing_answer:
                # Update existing answer
                existing_answer.user_answer = answer
                existing_answer.is_correct = is_correct  # Предполагаем, что в DBAnswer есть это поле
                existing_answer.score = score  # Предполагаем, что в DBAnswer есть это поле
                existing_answer.updated_at = datetime.datetime.now()
            else:
                # Create new answer
                answer_obj = DBAnswer(
                    problem_id=problem_id,
                    user_id=user_id,
                    user_answer=answer,
                    is_correct=is_correct,
                    score=score,
                    timestamp=datetime.datetime.now(),
                )
                session.add(answer_obj)

            session.commit()

    # Legacy methods for backward compatibility
    def save_problem(self, problem: DomainProblem) -> None:
        """Legacy method to save a problem - kept for backward compatibility."""
        # Create a new synchronous save method for legacy compatibility
        db_problem = domain_to_db_problem(problem)
        
        with self.SessionLocal() as session:
            # Check if problem already exists
            existing = session.query(DBProblem).filter(DBProblem.problem_id == problem.problem_id.value).first()
            if existing:
                # Update existing problem
                for field in ['subject', 'type', 'text', 'answer', 'options', 'solutions',
                              'topics', 'difficulty_level', 'task_number',
                              'kes_codes', 'kos_codes', 'exam_part', 'max_score', 'form_id', 'source_url',
                              'raw_html_path', 'updated_at', 'metadata_']:
                    setattr(existing, field, getattr(db_problem, field))
            else:
                # Add new problem
                session.add(db_problem)
            session.commit()

    def get_problem_by_id(self, problem_id: str) -> Optional[DomainProblem]:
        """Legacy method to get a problem by ID - kept for backward compatibility."""
        with self.SessionLocal() as session:
            db_problem = session.query(DBProblem).filter(DBProblem.problem_id == problem_id).first()
            if db_problem:
                return db_to_domain_problem(db_problem)
        return None

    def get_problems_by_subject(self, subject: str) -> List[DomainProblem]:
        """Legacy method to get problems by subject - kept for backward compatibility."""
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.subject == subject).all()
            return [db_to_domain_problem(db) for db in db_problems]

    def save_answer(self, problem_id: str, answer: str, user_id: str = "default"):
        """Save an answer for a problem."""
        with self.SessionLocal() as session:
            # Check if answer already exists for this user and problem
            existing_answer = (
                session.query(DBAnswer)
                .filter(DBAnswer.problem_id == problem_id, DBAnswer.user_id == user_id)
                .first()
            )

            if existing_answer:
                # Update existing answer
                existing_answer.user_answer = answer
                existing_answer.updated_at = datetime.datetime.now()
            else:
                # Create new answer
                answer_obj = DBAnswer(
                    problem_id=problem_id,
                    user_id=user_id,
                    user_answer=answer,
                    timestamp=datetime.datetime.now(),
                )
                session.add(answer_obj)

            session.commit()


    async def get_answer_status(self, problem_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the answer status for a problem and user."""
        if self.async_engine is None:
            # В тестах используем синхронный сеанс
            with self.SessionLocal() as session:
                result = session.query(DBAnswer).filter(
                    DBAnswer.problem_id == problem_id,
                    DBAnswer.user_id == user_id
                ).first()
                
                if result:
                    return {
                        "user_answer": result.user_answer,
                        "status": result.status,
                        "is_correct": result.is_correct,
                        "score": result.score,
                        "timestamp": result.timestamp
                    }
                return None
        else:
            # В продакшене используем асинхронный сеанс
            async with self.async_session() as session:
                result = await session.execute(
                    sa.select(DBAnswer).filter(
                        DBAnswer.problem_id == problem_id,
                        DBAnswer.user_id == user_id
                    )
                )
                answer = result.scalars().first()
                
                if answer:
                    return {
                        "user_answer": answer.user_answer,
                        "status": answer.status,
                        "is_correct": answer.is_correct,
                        "score": answer.score,
                        "timestamp": answer.timestamp
                    }
                return None

    def get_all_subjects(self) -> List[str]:
        """Get all available subjects from the database."""
        with self.SessionLocal() as session:
            subjects = session.query(DBProblem.subject).distinct().all()
            return [subject for subject, in subjects if subject]  # Извлекаем значения из кортежей и фильтруем None
    
    def get_random_problem_ids(self, subject: str, count: int) -> List[str]:
        """Get random problem IDs for a given subject."""
        with self.SessionLocal() as session:
            # Получаем случайные задачи для указанного предмета
            # Используем func.random() для случайной сортировки и limit для ограничения количества
            db_problems = session.query(DBProblem.problem_id).filter(
                DBProblem.subject == subject
            ).order_by(sa.func.random()).limit(count).all()
            
            # Извлекаем ID задач из кортежей
            return [problem_id for problem_id, in db_problems]
