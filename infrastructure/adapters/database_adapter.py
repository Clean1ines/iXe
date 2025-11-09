"""
Infrastructure adapter for managing SQLite connections and performing CRUD operations
on tasks and answers using SQLAlchemy ORM.
"""

import datetime
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from domain.models.database_models import Base, DBProblem, DBAnswer
from domain.models.problem_schema import Problem
from utils.model_adapter import db_problem_to_problem
from domain.interfaces.infrastructure_adapters import IDatabaseProvider


logger = logging.getLogger(__name__)


class DatabaseAdapter(IDatabaseProvider):
    """
    Class for managing SQLite database using SQLAlchemy ORM.

    Encapsulates database connection, table creation, and core operations:
    saving tasks and answers, retrieving tasks and answer statuses.
    Implements IDatabaseProvider interface which acts as repository interface.
    """

    def __init__(self, db_path: str = "data/fipi_data.db"):
        self.db_path = db_path
        self.engine = sa.create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._ensure_tables()

    def _ensure_tables(self):
        """Create tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def save_problem(self, problem: Problem) -> None:
        """
        Save a problem to the database.

        Args:
            problem: Problem instance to save.
        """
        db_problem = DBProblem(
            id=problem.problem_id,
            subject=problem.subject,
            type=problem.type,
            text=problem.text,
            answer=problem.answer,
            options=problem.options,
            solutions=problem.solutions,
            kes_codes=problem.kes_codes,
            skills=problem.skills,
            difficulty_level=problem.difficulty_level,
            task_number=problem.task_number,
            kos_codes=problem.kos_codes,
            exam_part=problem.exam_part,
            max_score=problem.max_score,
            form_id=problem.form_id,
            source_url=problem.source_url,
            raw_html_path=problem.raw_html_path,
            created_at=problem.created_at,
            updated_at=problem.updated_at,
            metadata=problem.metadata,
        )

        with self.SessionLocal() as session:
            # Check if problem already exists
            existing = session.query(DBProblem).filter(DBProblem.id == problem.problem_id).first()
            if existing:
                # Update existing problem
                for field in ['subject', 'type', 'text', 'answer', 'options', 'solutions',
                              'kes_codes', 'skills', 'difficulty_level', 'task_number',
                              'kos_codes', 'exam_part', 'max_score', 'form_id', 'source_url',
                              'raw_html_path', 'updated_at', 'metadata']:
                    setattr(existing, field, getattr(db_problem, field))
            else:
                # Add new problem
                session.add(db_problem)
            session.commit()

    async def save(self, problem: Problem) -> None:
        """Async save method."""
        self.save_problem(problem)

    def get_problem(self, problem_id: str) -> Optional[Problem]:
        """
        Retrieve a problem by its ID.

        Args:
            problem_id: The ID of the problem to retrieve.

        Returns:
            Problem instance if found, None otherwise.
        """
        with self.SessionLocal() as session:
            db_problem = session.query(DBProblem).filter(DBProblem.id == problem_id).first()
            if db_problem:
                return db_problem_to_problem(db_problem)
        return None

    def get_problems_by_subject(self, subject: str) -> List[Problem]:
        """
        Retrieve all problems for a given subject.

        Args:
            subject: The subject to filter problems by.

        Returns:
            List of Problem instances.
        """
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).filter(DBProblem.subject == subject).all()
            return [db_problem_to_problem(db) for db in db_problems]

    def save_answer(self, problem_id: str, answer: str, user_id: str = "default"):
        """
        Save an answer for a problem.

        Args:
            problem_id: ID of the problem being answered.
            answer: The answer text.
            user_id: ID of the user providing the answer.
        """
        with self.SessionLocal() as session:
            # Check if answer already exists for this user and problem
            existing_answer = (
                session.query(DBAnswer)
                .filter(DBAnswer.problem_id == problem_id, DBAnswer.user_id == user_id)
                .first()
            )

            if existing_answer:
                # Update existing answer
                existing_answer.answer = answer
                existing_answer.updated_at = datetime.datetime.now()
            else:
                # Create new answer
                answer_obj = DBAnswer(
                    problem_id=problem_id,
                    user_id=user_id,
                    answer=answer,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now(),
                )
                session.add(answer_obj)

            session.commit()

    def get_answer_status(self, problem_id: str, user_id: str = "default") -> Optional[str]:
        """
        Retrieve the answer status for a problem.

        Args:
            problem_id: ID of the problem.
            user_id: ID of the user.

        Returns:
            Answer text if found, None otherwise.
        """
        with self.SessionLocal() as session:
            answer = (
                session.query(DBAnswer)
                .filter(DBAnswer.problem_id == problem_id, DBAnswer.user_id == user_id)
                .first()
            )
            return answer.answer if answer else None

    def get_all_answers(self, user_id: str = "default") -> List[Tuple[str, str, str]]:
        """
        Retrieve all answers for a user.

        Args:
            user_id: ID of the user.

        Returns:
            List of tuples (problem_id, answer, timestamp).
        """
        with self.SessionLocal() as session:
            answers = (
                session.query(DBAnswer.problem_id, DBAnswer.answer, DBAnswer.updated_at)
                .filter(DBAnswer.user_id == user_id)
                .all()
            )
            return [(ans.problem_id, ans.answer, str(ans.updated_at)) for ans in answers]

    def get_all_problems(self) -> List[Problem]:
        """
        Retrieve all problems from the database.

        Returns:
            List of Problem instances.
        """
        with self.SessionLocal() as session:
            db_problems = session.query(DBProblem).all()
            return [db_problem_to_problem(db) for db in db_problems]

    def get_problems_by_task_number(self, subject: str, task_number: int) -> List[Problem]:
        """
        Retrieve problems by subject and task number.

        Args:
            subject: The subject to filter by.
            task_number: The task number to filter by.

        Returns:
            List of Problem instances.
        """
        with self.SessionLocal() as session:
            db_problems = (
                session.query(DBProblem)
                .filter(DBProblem.subject == subject, DBProblem.task_number == task_number)
                .all()
            )
            return [db_problem_to_problem(db) for db in db_problems]

    def get_random_problems_by_subject(self, subject: str, count: int) -> List[Problem]:
        """
        Retrieve a random set of problems by subject.

        Args:
            subject: The subject to filter by.
            count: Number of problems to retrieve.

        Returns:
            List of Problem instances.
        """
        with self.SessionLocal() as session:
            import random
            db_problems = (
                session.query(DBProblem)
                .filter(DBProblem.subject == subject)
                .order_by(sa.func.random())
                .limit(count)
                .all()
            )
            return [db_problem_to_problem(db) for db in db_problems]

    def get_problem_count_by_subject(self, subject: str) -> int:
        """
        Get the total count of problems for a subject.

        Args:
            subject: The subject to count problems for.

        Returns:
            Number of problems for the subject.
        """
        with self.SessionLocal() as session:
            count = session.query(DBProblem).filter(DBProblem.subject == subject).count()
            return count
