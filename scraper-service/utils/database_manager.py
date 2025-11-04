"""
Module for managing database connections and performing CRUD operations
on tasks and answers using SQLAlchemy ORM, compatible with Supabase.
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
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Class for managing database connections (Supabase/PostgreSQL) using SQLAlchemy ORM.
    Encapsulates database connection, table creation, and core operations:
    saving tasks and answers, retrieving tasks and answer statuses.
    """
    def __init__(self, connection_string: str = None):
        """
        Initializes the manager with the specified connection string.
        If no connection string is provided, attempts to use Supabase client.
        Args:
            connection_string (str, optional): Database connection string. Defaults to None.
        """
        self.supabase_client: Client = None
        self.engine = None
        self.SessionLocal = None
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            try:
                self.supabase_client = create_client(supabase_url, supabase_key)
                logger.info("DatabaseManager initialized with Supabase client.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                # Fallback to SQLAlchemy if Supabase init fails
                self._init_sqlalchemy(connection_string)
        else:
            self._init_sqlalchemy(connection_string)
    
    def _init_sqlalchemy(self, connection_string: str):
        """Initialize SQLAlchemy engine and session."""
        if not connection_string:
            connection_string = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        self.engine = sa.create_engine(connection_string, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.debug(f"DatabaseManager initialized with SQLAlchemy engine using connection string: {connection_string}")

    def initialize_db(self) -> None:
        """Creates database tables if they do not exist yet."""
        logger.info("Initializing database tables...")
        if self.engine:
            try:
                Base.metadata.create_all(self.engine)
                logger.info("Database tables initialized (or verified to exist).")
            except Exception as e:
                logger.error(f"Error initializing database: {e}", exc_info=True)
                raise
        else:
            logger.warning("No SQLAlchemy engine available, skipping table creation.")

    def save_problems(self, problems: List[Problem]) -> None:
        """Saves a list of problems to the database."""
        logger.info(f"Saving {len(problems)} problems to database...")
        if self.engine:
            self._save_problems_sqlalchemy(problems)
        elif self.supabase_client:
            self._save_problems_supabase(problems)
        else:
            raise RuntimeError("No database client available (neither SQLAlchemy engine nor Supabase client)")

    def _save_problems_sqlalchemy(self, problems: List[Problem]) -> None:
        """Saves problems using SQLAlchemy ORM."""
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
                        'solutions': None,  # SQLAlchemy model doesn't have this field
                        'topics': prob.kes_codes,
                        'skills': None,  # SQLAlchemy model doesn't have this field
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
            logger.info(f"Successfully saved {len(problems)} problems to database via SQLAlchemy.")
        except Exception as e:
            logger.error(f"Error saving problems via SQLAlchemy: {e}", exc_info=True)
            raise

    def _save_problems_supabase(self, problems: List[Problem]) -> None:
        """Saves problems using Supabase client."""
        try:
            problem_dicts = [
                {
                    'problem_id': prob.problem_id,
                    'subject': prob.subject,
                    'type': prob.type,
                    'text': prob.text,
                    'options': prob.options,
                    'answer': prob.answer,
                    'solutions': None,  # Not in current model
                    'topics': prob.kes_codes,
                    'skills': None,  # Not in current model
                    'difficulty_level': prob.difficulty_level,
                    'task_number': prob.task_number,
                    'kes_codes': prob.kes_codes,
                    'kos_codes': prob.kos_codes,
                    'exam_part': prob.exam_part,
                    'max_score': prob.max_score,
                    'form_id': prob.form_id,
                    'source_url': prob.source_url,
                    'raw_html_path': prob.raw_html_path,
                    'created_at': prob.created_at.isoformat() if prob.created_at else None,
                    'updated_at': prob.updated_at.isoformat() if prob.updated_at else None,
                    'metadata_': prob.metadata,
                }
                for prob in problems
            ]
            
            # Assuming a table named 'problems' in Supabase
            response = self.supabase_client.table('problems').upsert(problem_dicts).execute()
            logger.info(f"Successfully saved {len(problems)} problems to database via Supabase.")
        except Exception as e:
            logger.error(f"Error saving problems via Supabase: {e}", exc_info=True)
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
        if self.engine:
            self._save_answer_sqlalchemy(task_id, user_id, user_answer, status)
        elif self.supabase_client:
            self._save_answer_supabase(task_id, user_id, user_answer, status)
        else:
            raise RuntimeError("No database client available (neither SQLAlchemy engine nor Supabase client)")

    def _save_answer_sqlalchemy(self, task_id: str, user_id: str, user_answer: str, status: str) -> None:
        """Saves answer using SQLAlchemy ORM."""
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
            logger.info(f"Successfully saved answer for task {task_id} via SQLAlchemy.")
        except Exception as e:
            logger.error(f"Error saving answer via SQLAlchemy: {e}", exc_info=True)
            raise

    def _save_answer_supabase(self, task_id: str, user_id: str, user_answer: str, status: str) -> None:
        """Saves answer using Supabase client."""
        try:
            answer_dict = {
                'problem_id': task_id,
                'user_id': user_id,
                'user_answer': user_answer,
                'status': status,
                'timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
            }
            
            response = self.supabase_client.table('answers').upsert(answer_dict).execute()
            logger.info(f"Successfully saved answer for task {task_id} via Supabase.")
        except Exception as e:
            logger.error(f"Error saving answer via Supabase: {e}", exc_info=True)
            raise

    def get_answer_and_status(
        self, task_id: str, user_id: str
    ) -> Tuple[Optional[str], str]:
        """Gets the answer and status by task identifier."""
        if self.engine:
            return self._get_answer_and_status_sqlalchemy(task_id, user_id)
        elif self.supabase_client:
            return self._get_answer_and_status_supabase(task_id, user_id)
        else:
            raise RuntimeError("No database client available (neither SQLAlchemy engine nor Supabase client)")

    def _get_answer_and_status_sqlalchemy(self, task_id: str, user_id: str) -> Tuple[Optional[str], str]:
        """Gets answer and status using SQLAlchemy ORM."""
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
            logger.error(f"Error fetching answer via SQLAlchemy: {e}", exc_info=True)
            raise

    def _get_answer_and_status_supabase(self, task_id: str, user_id: str) -> Tuple[Optional[str], str]:
        """Gets answer and status using Supabase client."""
        try:
            response = self.supabase_client.table('answers').select('user_answer, status').eq('problem_id', task_id).eq('user_id', user_id).execute()
            if response.data:
                row = response.data[0]
                return row['user_answer'], row['status']
            return None, "not_checked"
        except Exception as e:
            logger.error(f"Error fetching answer via Supabase: {e}", exc_info=True)
            raise

    def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """Gets a problem by its identifier."""
        if self.engine:
            return self._get_problem_by_id_sqlalchemy(problem_id)
        elif self.supabase_client:
            return self._get_problem_by_id_supabase(problem_id)
        else:
            raise RuntimeError("No database client available (neither SQLAlchemy engine nor Supabase client)")

    def _get_problem_by_id_sqlalchemy(self, problem_id: str) -> Optional[Problem]:
        """Gets a problem by its identifier using SQLAlchemy ORM."""
        try:
            with self.SessionLocal() as session:
                db_problem = session.query(DBProblem).filter_by(problem_id=problem_id).first()
                if db_problem:
                    return db_problem_to_problem(db_problem)
                return None
        except Exception as e:
            logger.error(f"Error fetching problem via SQLAlchemy: {e}", exc_info=True)
            raise

    def _get_problem_by_id_supabase(self, problem_id: str) -> Optional[Problem]:
        """Gets a problem by its identifier using Supabase client."""
        try:
            response = self.supabase_client.table('problems').select('*').eq('problem_id', problem_id).execute()
            if response.data:
                row = response.data[0]
                # Map Supabase row to DBProblem object, then to Problem
                db_prob = DBProblem(
                    problem_id=row['problem_id'],
                    subject=row['subject'],
                    type=row['type'],
                    text=row['text'],
                    options=row['options'],
                    answer=row['answer'],
                    difficulty_level=row['difficulty_level'],
                    task_number=row['task_number'],
                    kes_codes=row['kes_codes'],
                    kos_codes=row['kos_codes'],
                    exam_part=row['exam_part'],
                    max_score=row['max_score'],
                    form_id=row['form_id'],
                    source_url=row['source_url'],
                    raw_html_path=row['raw_html_path'],
                    created_at=datetime.datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                    metadata_=row['metadata_']
                )
                return db_problem_to_problem(db_prob)
            return None
        except Exception as e:
            logger.error(f"Error fetching problem via Supabase: {e}", exc_info=True)
            raise

    def get_problems_by_ids(self, problem_ids: List[str]) -> List[Problem]:
        """
        Gets multiple problems by their identifiers in a single query.
        """
        if self.engine:
            return self._get_problems_by_ids_sqlalchemy(problem_ids)
        elif self.supabase_client:
            return self._get_problems_by_ids_supabase(problem_ids)
        else:
            raise RuntimeError("No database client available (neither SQLAlchemy engine nor Supabase client)")

    def _get_problems_by_ids_sqlalchemy(self, problem_ids: List[str]) -> List[Problem]:
        """Gets multiple problems by their identifiers using SQLAlchemy ORM."""
        if not problem_ids:
            return []
        try:
            with self.SessionLocal() as session:
                db_problems = session.query(DBProblem).filter(DBProblem.problem_id.in_(problem_ids)).all()
                problems = [db_problem_to_problem(db_prob) for db_prob in db_problems]
                logger.debug(f"Fetched {len(problems)} problems out of {len(problem_ids)} requested IDs via SQLAlchemy.")
                return problems
        except Exception as e:
            logger.error(f"Error fetching problems by IDs via SQLAlchemy: {e}", exc_info=True)
            raise

    def _get_problems_by_ids_supabase(self, problem_ids: List[str]) -> List[Problem]:
        """Gets multiple problems by their identifiers using Supabase client."""
        if not problem_ids:
            return []
        try:
            response = self.supabase_client.table('problems').select('*').in_('problem_id', problem_ids).execute()
            problems = []
            for row in response.data:
                db_prob = DBProblem(
                    problem_id=row['problem_id'],
                    subject=row['subject'],
                    type=row['type'],
                    text=row['text'],
                    options=row['options'],
                    answer=row['answer'],
                    difficulty_level=row['difficulty_level'],
                    task_number=row['task_number'],
                    kes_codes=row['kes_codes'],
                    kos_codes=row['kos_codes'],
                    exam_part=row['exam_part'],
                    max_score=row['max_score'],
                    form_id=row['form_id'],
                    source_url=row['source_url'],
                    raw_html_path=row['raw_html_path'],
                    created_at=datetime.datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                    metadata_=row['metadata_']
                )
                problems.append(db_problem_to_problem(db_prob))
            logger.debug(f"Fetched {len(problems)} problems out of {len(problem_ids)} requested IDs via Supabase.")
            return problems
        except Exception as e:
            logger.error(f"Error fetching problems by IDs via Supabase: {e}", exc_info=True)
            raise

    def get_all_problems(self) -> List[Problem]:
        """Gets all problems from the database."""
        if self.engine:
            return self._get_all_problems_sqlalchemy()
        elif self.supabase_client:
            return self._get_all_problems_supabase()
        else:
            raise RuntimeError("No database client available (neither SQLAlchemy engine nor Supabase client)")

    def _get_all_problems_sqlalchemy(self) -> List[Problem]:
        """Gets all problems from the database using SQLAlchemy ORM."""
        try:
            with self.SessionLocal() as session:
                db_problems = session.query(DBProblem).all()
                return [db_problem_to_problem(p) for p in db_problems]
        except Exception as e:
            logger.error(f"Error fetching all problems via SQLAlchemy: {e}", exc_info=True)
            raise

    def _get_all_problems_supabase(self) -> List[Problem]:
        """Gets all problems from the database using Supabase client."""
        try:
            response = self.supabase_client.table('problems').select('*').execute()
            problems = []
            for row in response.data:
                db_prob = DBProblem(
                    problem_id=row['problem_id'],
                    subject=row['subject'],
                    type=row['type'],
                    text=row['text'],
                    options=row['options'],
                    answer=row['answer'],
                    difficulty_level=row['difficulty_level'],
                    task_number=row['task_number'],
                    kes_codes=row['kes_codes'],
                    kos_codes=row['kos_codes'],
                    exam_part=row['exam_part'],
                    max_score=row['max_score'],
                    form_id=row['form_id'],
                    source_url=row['source_url'],
                    raw_html_path=row['raw_html_path'],
                    created_at=datetime.datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                    metadata_=row['metadata_']
                )
                problems.append(db_problem_to_problem(db_prob))
            return problems
        except Exception as e:
            logger.error(f"Error fetching all problems via Supabase: {e}", exc_info=True)
            raise

    def get_all_subjects(self) -> List[str]:
        """Returns a list of all unique subjects in the database."""
        if self.engine:
            return self._get_all_subjects_sqlalchemy()
        elif self.supabase_client:
            return self._get_all_subjects_supabase()
        else:
            raise RuntimeError("No database client available (neither SQLAlchemy engine nor Supabase client)")

    def _get_all_subjects_sqlalchemy(self) -> List[str]:
        """Returns a list of all unique subjects using SQLAlchemy."""
        try:
            with self.SessionLocal() as session:
                result = session.execute(sa.text("SELECT DISTINCT subject FROM problems WHERE subject IS NOT NULL"))
                return [row[0] for row in result.fetchall() if row[0]]
        except Exception as e:
            logger.error(f"Error fetching subjects via SQLAlchemy: {e}", exc_info=True)
            raise

    def _get_all_subjects_supabase(self) -> List[str]:
        """Returns a list of all unique subjects using Supabase."""
        try:
            response = self.supabase_client.table('problems').select('subject').execute()
            subjects = set()
            for row in response.data:
                if row['subject']:
                    subjects.add(row['subject'])
            return list(subjects)
        except Exception as e:
            logger.error(f"Error fetching subjects via Supabase: {e}", exc_info=True)
            raise

    def get_random_problem_ids(self, subject: str, count: int = 10) -> List[str]:
        """Returns `count` random problem_ids for the given subject."""
        if self.engine:
            return self._get_random_problem_ids_sqlalchemy(subject, count)
        elif self.supabase_client:
            return self._get_random_problem_ids_supabase(subject, count)
        else:
            raise RuntimeError("No database client available (neither SQLAlchemy engine nor Supabase client)")

    def _get_random_problem_ids_sqlalchemy(self, subject: str, count: int = 10) -> List[str]:
        """Returns random problem_ids using SQLAlchemy."""
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
            logger.error(f"Error fetching random problem IDs via SQLAlchemy: {e}", exc_info=True)
            raise

    def _get_random_problem_ids_supabase(self, subject: str, count: int = 10) -> List[str]:
        """Returns random problem_ids using Supabase."""
        try:
            response = self.supabase_client.table('problems').select('problem_id').eq('subject', subject).order('random()', desc=False).limit(count).execute()
            return [row['problem_id'] for row in response.data]
        except Exception as e:
            logger.error(f"Error fetching random problem IDs via Supabase: {e}", exc_info=True)
            raise
