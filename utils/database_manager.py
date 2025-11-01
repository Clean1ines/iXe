"""
Module for managing SQLite connections and performing CRUD operations
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

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Class for managing SQLite database using SQLAlchemy ORM.

    Encapsulates database connection, table creation, and core operations:
    saving tasks and answers, retrieving tasks and answer statuses.
    """

    def __init__(self, db_path: str):
        """Initializes the manager with the specified path to the SQLite file.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.engine = sa.create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.debug(f"DatabaseManager initialized with path: {db_path}")

    def initialize_db(self) -> None:
        """Creates database tables if they do not exist yet."""
        logger.info("Initializing database tables...")
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized (or verified to exist).")
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

    def save_problems(self, problems: List[Problem]) -> None:
        """Saves a list of tasks to the database.

        If a task with the same `problem_id` already exists, it will be replaced.

        Args:
            problems (List[Problem]): List of Pydantic task models.
        """
        logger.info(f"Saving {len(problems)} problems to database...")
        try:
            with self.SessionLocal() as session:
                problem_mappings = [
                    {
                        'problem_id': prob.problem_id,
                        'subject': prob.subject,
                        'type': prob.type,
                        'text': prob.text,
                        'options': prob.options,
                        'answer': prob.answer,
                        'solutions': prob.solutions,
                        'topics': prob.topics,
                        'skills': prob.skills,
                        'difficulty_level': prob.difficulty_level,
                        'task_number': prob.task_number,
                        'kes_codes': prob.kes_codes,
                        'kos_codes': prob.kos_codes,
                        'exam_part': prob.exam_part,
                        'max_score': prob.max_score,
                        'form_id': prob.form_id,
                        'source_url': prob.source_url,
                        'raw_html_path': prob.raw_html_path,
                        'created_at': prob.created_at,
                        'updated_at': prob.updated_at,
                        'metadata_': prob.metadata,
                    }
                    for prob in problems
                ]
                session.bulk_insert_mappings(DBProblem, problem_mappings)
                session.commit()
            logger.info(f"Successfully saved {len(problems)} problems to database.")
        except Exception as e:
            logger.error(f"Error saving problems to database: {e}", exc_info=True)
            raise

    def save_answer(
        self,
        task_id: str,
        user_id: str,
        user_answer: str,
        status: str = "not_checked",
    ) -> None:
        """Saves or updates a user's answer to a task."""
        logger.info(f"Saving answer for task {task_id}, user {user_id}, status {status}.")
        try:
            with self.SessionLocal() as session:
                db_answer = DBAnswer(
                    problem_id=task_id,
                    user_id=user_id,
                    user_answer=user_answer,
                    status=status,
                    timestamp=datetime.datetime.now(datetime.UTC),
                )
                session.merge(db_answer)
                session.commit()
            logger.info(f"Successfully saved answer for task {task_id}.")
        except Exception as e:
            logger.error(f"Error saving answer for task {task_id}: {e}", exc_info=True)
            raise

    def get_answer_and_status(
        self, task_id: str, user_id: str
    ) -> Tuple[Optional[str], str]:
        """Gets the answer and status by task identifier."""
        try:
            with self.SessionLocal() as session:
                db_answer = (
                    session.query(DBAnswer)
                    .filter_by(problem_id=task_id, user_id=user_id)
                    .first()
                )
                if db_answer:
                    return db_answer.user_answer, db_answer.status
                return None, "not_checked"
        except Exception as e:
            logger.error(f"Error fetching answer for task {task_id}: {e}", exc_info=True)
            raise

    def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """Gets a task by its identifier."""
        try:
            with self.SessionLocal() as session:
                db_problem = session.query(DBProblem).filter_by(problem_id=problem_id).first()
                if db_problem:
                    return Problem(
                        problem_id=db_problem.problem_id,
                        subject=db_problem.subject,
                        type=db_problem.type,
                        text=db_problem.text,
                        options=db_problem.options,
                        answer=db_problem.answer,
                        solutions=db_problem.solutions,
                        topics=db_problem.topics,
                        skills=db_problem.skills,
                        difficulty_level=db_problem.difficulty_level,
                        task_number=db_problem.task_number,
                        kes_codes=db_problem.kes_codes,
                        kos_codes=db_problem.kos_codes,
                        exam_part=db_problem.exam_part,
                        max_score=db_problem.max_score,
                        form_id=db_problem.form_id,
                        source_url=db_problem.source_url,
                        raw_html_path=db_problem.raw_html_path,
                        created_at=db_problem.created_at,
                        updated_at=db_problem.updated_at,
                        metadata=db_problem.metadata_,
                    )
                return None
        except Exception as e:
            logger.error(f"Error fetching problem {problem_id}: {e}", exc_info=True)
            raise

    def get_all_problems(self) -> List[Problem]:
        """Gets all tasks from the database."""
        try:
            with self.SessionLocal() as session:
                db_problems = session.query(DBProblem).all()
                return [
                    Problem(
                        problem_id=p.problem_id,
                        subject=p.subject,
                        type=p.type,
                        text=p.text,
                        options=p.options,
                        answer=p.answer,
                        solutions=p.solutions,
                        topics=p.topics,
                        skills=p.skills,
                        difficulty_level=p.difficulty_level,
                        task_number=p.task_number,
                        kes_codes=p.kes_codes,
                        kos_codes=p.kos_codes,
                        exam_part=p.exam_part,
                        max_score=p.max_score,
                        form_id=p.form_id,
                        source_url=p.source_url,
                        raw_html_path=p.raw_html_path,
                        created_at=p.created_at,
                        updated_at=p.updated_at,
                        metadata=p.metadata_,
                    )
                    for p in db_problems
                ]
        except Exception as e:
            logger.error(f"Error fetching all problems: {e}", exc_info=True)
            raise

    def get_all_subjects(self) -> List[str]:
        """Returns a list of all unique subjects in the database."""
        try:
            with self.SessionLocal() as session:
                result = session.execute(sa.text("SELECT DISTINCT subject FROM problems WHERE subject IS NOT NULL"))
                return [row[0] for row in result.fetchall() if row[0]]
        except Exception as e:
            logger.error(f"Error fetching subjects: {e}", exc_info=True)
            raise

    def get_random_problem_ids(self, subject: str, count: int = 10) -> List[str]:
        """Returns `count` random problem_ids for the given subject."""
        try:
            with self.SessionLocal() as session:
                result = session.execute(
                    sa.text("""
                        SELECT problem_id 
                        FROM problems 
                        WHERE subject = :subject 
                        ORDER BY RANDOM() 
                        LIMIT :count
                    """),
                    {"subject": subject, "count": count}
                )
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching random problem IDs for subject {subject}: {e}", exc_info=True)
            raise
