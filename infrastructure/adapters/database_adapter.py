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
        await self.save_problem(problem)  # Используем существующий метод для обратной совместимости

    async def get_by_id(self, problem_id: ProblemId) -> Optional[DomainProblem]:
        """Retrieve a problem by its ID."""
        with self.SessionLocal() as session:
            db_problem = session.query(DBProblem).filter(DBProblem.problem_id == str(problem_id)).first()
            if db_problem:
                return self._map_db_to_domain(db_problem)
        return None

    async def get_by_subject(self, subject: str) -> List[DomainProblem]:
        """Retrieve all problems for a given subject."""
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.subject == subject).all()
            return [self._map_db_to_domain(db) for db in db_problems]

    async def get_by_exam_part(self, exam_part: str) -> List[DomainProblem]:
        """Retrieve all problems for a given exam part."""
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.exam_part == exam_part).all()
            return [self._map_db_to_domain(db) for db in db_problems]

    async def get_by_difficulty(self, difficulty: str) -> List[DomainProblem]:
        """Retrieve all problems for a given difficulty level."""
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.difficulty_level == difficulty).all()
            return [self._map_db_to_domain(db) for db in db_problems]

    # IUserProgressRepository implementation
    async def save_user_progress(self, progress: DomainUserProgress) -> None:
        """Save a domain user progress entity to the database."""
        db_progress = self._map_domain_to_db_user_progress(progress)
        
        with self.SessionLocal() as session:
            # Check if progress already exists
            existing = session.query(DBUserProgress).filter(
                DBUserProgress.user_id == progress.user_id,
                DBUserProgress.problem_id == str(progress.problem_id.value) if hasattr(progress.problem_id, 'value') else str(progress.problem_id)
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
                return self._map_db_to_domain_user_progress(db_progress)
        return None

    async def get_user_progress_by_user(self, user_id: str) -> List[DomainUserProgress]:
        """Retrieve all progress records for a user."""
        with self.SessionLocal() as session:
            db_progresses = session.query(DBUserProgress).filter(DBUserProgress.user_id == user_id).all()
            return [self._map_db_to_domain_user_progress(db) for db in db_progresses]

    async def get_completed_user_progress_by_user(self, user_id: str) -> List[DomainUserProgress]:
        """Retrieve all completed progress records for a user."""
        with self.SessionLocal() as session:
            db_progresses = session.query(DBUserProgress).filter(
                DBUserProgress.user_id == user_id,
                DBUserProgress.status == 'COMPLETED'
            ).all()
            return [self._map_db_to_domain_user_progress(db) for db in db_progresses]

    # ISkillRepository implementation
    async def get_skill_by_id(self, skill_id: str) -> Optional[DomainSkill]:
        """Retrieve a skill by its ID."""
        with self.SessionLocal() as session:
            db_skill = session.query(DBSkill).filter(DBSkill.skill_id == skill_id).first()
            if db_skill:
                return self._map_db_to_domain_skill(db_skill)
        return None

    async def get_all_skills(self) -> List[DomainSkill]:
        """Retrieve all skills."""
        with self.SessionLocal() as session:
            db_skills = session.query(DBSkill).all()
            return [self._map_db_to_domain_skill(db_skill) for db_skill in db_skills]

    async def get_skills_by_problem_id(self, problem_id: str) -> List[DomainSkill]:
        """Retrieve all skills associated with a specific problem."""
        with self.SessionLocal() as session:
            db_skills = session.query(DBSkill).filter(
                DBSkill.related_problems.contains(problem_id)
            ).all()
            return [self._map_db_to_domain_skill(db_skill) for db_skill in db_skills]

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
                existing_answer.is_correct = is_correct
                existing_answer.score = score
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
    async def save_problem(self, problem: DomainProblem) -> None:
        """Save a domain problem to the database."""
        db_problem = self._map_domain_to_db(problem)
        
        with self.SessionLocal() as session:
            # Check if problem already exists - ИСПРАВЛЕНО: безопасное обращение к problem_id
            problem_id_value = problem.problem_id.value if hasattr(problem.problem_id, 'value') else problem.problem_id
            
            existing = session.query(DBProblem).filter(
                DBProblem.problem_id == str(problem_id_value)
            ).first()
            
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

    async def get_problem_by_id(self, problem_id: str) -> Optional[DomainProblem]:
        """Legacy method to get a problem by ID - kept for backward compatibility."""
        with self.SessionLocal() as session:
            db_problem = session.query(DBProblem).filter(DBProblem.problem_id == problem_id).first()
            if db_problem:
                return self._map_db_to_domain(db_problem)
        return None

    def get_problems_by_subject(self, subject: str) -> List[DomainProblem]:
        """Legacy method to get problems by subject - kept for backward compatibility."""
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.subject == subject).all()
            return [self._map_db_to_domain(db) for db in db_problems]

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

    # Внутренние методы маппинга - скрыты от внешнего мира
    def _map_domain_to_db(self, domain_problem: DomainProblem) -> DBProblem:
        """Преобразует domain Problem в DBProblem."""
        # ИСПРАВЛЕНО: безопасное обращение к problem_id.value
        problem_id_value = domain_problem.problem_id.value if hasattr(domain_problem.problem_id, 'value') else domain_problem.problem_id
        
        return DBProblem(
            problem_id=str(problem_id_value),
            subject=domain_problem.subject,
            type=str(domain_problem.problem_type.value.name) if hasattr(domain_problem.problem_type.value, 'name') else str(domain_problem.problem_type.value),
            text=domain_problem.text,
            options=domain_problem.options,
            answer=domain_problem.answer,
            topics=domain_problem.topics or (domain_problem.kes_codes if hasattr(domain_problem, 'kes_codes') else []),
            solutions=domain_problem.solutions,
            kes_codes=domain_problem.kes_codes if hasattr(domain_problem, 'kes_codes') else [],
            skills=domain_problem.skills if hasattr(domain_problem, 'skills') else None,
            difficulty_level=str(domain_problem.difficulty_level.value.name).lower() if hasattr(domain_problem.difficulty_level.value, 'name') else str(domain_problem.difficulty_level.value).lower(),
            task_number=domain_problem.task_number if hasattr(domain_problem, 'task_number') else None,
            kos_codes=domain_problem.kos_codes if hasattr(domain_problem, 'kos_codes') else [],
            exam_part=str(domain_problem.exam_part.value) if hasattr(domain_problem.exam_part, 'value') else str(domain_problem.exam_part),
            max_score=domain_problem.max_score,
            form_id=domain_problem.form_id if hasattr(domain_problem, 'form_id') else None,
            source_url=domain_problem.source_url if hasattr(domain_problem, 'source_url') else None,
            raw_html_path=domain_problem.raw_html_path if hasattr(domain_problem, 'raw_html_path') else None,
            created_at=domain_problem.created_at,
            updated_at=domain_problem.updated_at,
            metadata_=domain_problem.metadata if hasattr(domain_problem, 'metadata') else None
        )
    
    def _map_db_to_domain(self, db_problem: DBProblem) -> DomainProblem:
        """Преобразует DBProblem в domain Problem."""
        from domain.value_objects import (
            ProblemType, DifficultyLevel, ProblemStatus,
            ExamPart
        )
        from domain.value_objects.problem_id import ProblemId
        
        try:
            # Восстанавливаем Value Objects
            problem_type = ProblemType.from_string(db_problem.type) if hasattr(ProblemType, 'from_string') else ProblemType(db_problem.type)
            difficulty_level = DifficultyLevel.from_string(db_problem.difficulty_level) if hasattr(DifficultyLevel, 'from_string') else DifficultyLevel(db_problem.difficulty_level)
            # ExamPart пока строка, но в будущем будет VO
            exam_part = db_problem.exam_part
            problem_id = ProblemId(db_problem.problem_id)
            
            # Default status - DRAFT если не указано
            from domain.value_objects.problem_status import ProblemStatusEnum
            status = ProblemStatus(ProblemStatusEnum.DRAFT)
            
            # Создаем domain сущность
            return DomainProblem(
                problem_id=problem_id,
                subject=db_problem.subject,
                problem_type=problem_type,
                text=db_problem.text,
                difficulty_level=difficulty_level,
                exam_part=exam_part,
                max_score=db_problem.max_score,
                status=status,
                answer=db_problem.answer,
                options=db_problem.options,
                solutions=db_problem.solutions,
                kes_codes=db_problem.kes_codes or [],
                skills=db_problem.skills,
                task_number=db_problem.task_number,
                kos_codes=db_problem.kos_codes or [],
                form_id=db_problem.form_id,
                source_url=db_problem.source_url,
                raw_html_path=db_problem.raw_html_path,
                created_at=db_problem.created_at,
                updated_at=db_problem.updated_at,
                metadata=db_problem.metadata_,
                topics=db_problem.topics or []
            )
        except Exception as e:
            logger.error(f"Failed to map DB problem to domain: {e}")
            raise
    
    def _map_domain_to_db_user_progress(self, domain_progress: DomainUserProgress) -> DBUserProgress:
        """Преобразует domain UserProgress в DBUserProgress."""
        problem_id_value = domain_progress.problem_id.value if hasattr(domain_progress.problem_id, 'value') else domain_progress.problem_id
        
        return DBUserProgress(
            user_id=domain_progress.user_id,
            problem_id=str(problem_id_value),
            status=domain_progress.status.value if hasattr(domain_progress.status, 'value') else domain_progress.status,
            score=domain_progress.score,
            attempts=domain_progress.attempts,
            last_attempt_at=domain_progress.last_attempt_at,
            started_at=domain_progress.started_at
        )
    
    def _map_db_to_domain_user_progress(self, db_progress: DBUserProgress) -> DomainUserProgress:
        """Преобразует DBUserProgress в domain UserProgress."""
        from domain.value_objects.problem_id import ProblemId
        from domain.models.user_progress import ProgressStatus
        
        return DomainUserProgress(
            user_id=db_progress.user_id,
            problem_id=ProblemId(db_progress.problem_id),
            status=ProgressStatus(db_progress.status),
            score=db_progress.score,
            attempts=db_progress.attempts,
            last_attempt_at=db_progress.last_attempt_at,
            started_at=db_progress.started_at
        )
    
    def _map_domain_to_db_skill(self, domain_skill: DomainSkill) -> DBSkill:
        """Преобразует domain Skill в DBSkill."""
        # Convert ProblemId list to string list
        problem_ids_str = [str(pid.value) if hasattr(pid, 'value') else str(pid) for pid in domain_skill.related_problems]
        
        return DBSkill(
            skill_id=domain_skill.skill_id,
            name=domain_skill.name,
            description=domain_skill.description,
            prerequisites=domain_skill.prerequisites,
            related_problems=problem_ids_str,
        )
    
    def _map_db_to_domain_skill(self, db_skill: DBSkill) -> DomainSkill:
        """Преобразует DBSkill в domain Skill."""
        from domain.value_objects.problem_id import ProblemId
        
        # Convert string list to ProblemId list
        problem_ids = [ProblemId(pid_str) for pid_str in db_skill.related_problems]
        
        return DomainSkill(
            skill_id=db_skill.skill_id,
            name=db_skill.name,
            description=db_skill.description,
            prerequisites=db_skill.prerequisites,
            related_problems=problem_ids,
        )