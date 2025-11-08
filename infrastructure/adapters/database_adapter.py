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

from models.database_models import Base, DBProblem, DBAnswer
from models.problem_schema import Problem
from utils.model_adapter import db_problem_to_problem
from domain.interfaces.infrastructure_adapters import IDatabaseProvider


logger = logging.getLogger(__name__)


class DatabaseAdapter(IDatabaseProvider):
    """
    Class for managing SQLite database using SQLAlchemy ORM.

    Encapsulates database connection, table creation, and core operations:
    saving tasks and answers, retrieving tasks and answer statuses.
    """

    def __init__(self, db_path: str):
        """Initializes the manager with the specified path to the SQLite file.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.engine = sa.create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Creates database tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)

    def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """Get problem by its ID."""
        with self.SessionLocal() as session:
            db_problem = session.query(DBProblem).filter(DBProblem.problem_id == problem_id).first()
            if db_problem:
                return db_problem_to_problem(db_problem)
            return None

    def save_problem(self, problem: Problem) -> None:
        """Save a problem to the database."""
        with self.SessionLocal() as session:
            # Convert Problem to DBProblem
            db_problem = DBProblem(
                problem_id=problem.problem_id,
                subject=problem.subject,
                content=problem.content,
                answer=problem.answer,
                task_number=problem.task_number,
                answer_type=problem.answer_type,
                kes_codes=problem.kes_codes,
                kos_codes=problem.kos_codes,
                difficulty=problem.difficulty,
                tags=problem.tags,
                metadata=problem.metadata
            )
            session.merge(db_problem)  # Use merge to handle both insert and update
            session.commit()

    def get_answer_status(self, problem_id: str) -> Optional[str]:
        """Get the status of an answer for a problem."""
        with self.SessionLocal() as session:
            answer_record = session.query(DBAnswer).filter(DBAnswer.problem_id == problem_id).first()
            if answer_record:
                return answer_record.status
            return None

    def save_answer_status(self, problem_id: str, status: str) -> None:
        """Save the status of an answer for a problem."""
        with self.SessionLocal() as session:
            answer_record = session.query(DBAnswer).filter(DBAnswer.problem_id == problem_id).first()
            if answer_record:
                answer_record.status = status
                answer_record.updated_at = datetime.datetime.utcnow()
            else:
                answer_record = DBAnswer(
                    problem_id=problem_id,
                    status=status,
                    updated_at=datetime.datetime.utcnow()
                )
                session.add(answer_record)
            session.commit()
