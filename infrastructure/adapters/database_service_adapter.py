"""
Infrastructure adapter for database operations.

This adapter implements the IDatabaseService interface using SQLAlchemy,
providing database persistence capabilities for scraping operations.
"""
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from domain.interfaces.external_services import IDatabaseService
from domain.models.problem import Problem
from domain.value_objects.problem_id import ProblemId
from domain.models.database_models import Base, DBProblem

logger = logging.getLogger(__name__)

class DatabaseServiceAdapter(IDatabaseService):
    """
    Adapter for database operations using SQLAlchemy.
    
    Business Rules:
    - Manages database connections properly
    - Handles schema initialization and migrations
    - Provides thread-safe session management
    - Ensures data integrity and consistency
    """
    
    def __init__(self, database_path: str):
        """
        Initialize database service adapter.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.engine = create_engine(f"sqlite:///{database_path}")
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        
        # Ensure database directory exists
        db_path = Path(database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def save_problem(self, problem: Problem) -> bool:
        """Save a problem to the database."""
        session = self.Session()
        try:
            # Convert domain problem to database model
            db_problem = self._map_domain_to_db(problem)
            
            # Check if problem exists
            existing = session.query(DBProblem).filter(
                DBProblem.problem_id == str(problem.problem_id.value)
            ).first()
            
            if existing:
                # Update existing problem
                for field in [
                    'subject', 'type', 'text', 'answer', 'options', 'solutions',
                    'topics', 'difficulty_level', 'task_number', 'kes_codes',
                    'kos_codes', 'exam_part', 'max_score', 'form_id', 'source_url',
                    'raw_html_path', 'updated_at', 'metadata_'
                ]:
                    setattr(existing, field, getattr(db_problem, field))
            else:
                # Add new problem
                session.add(db_problem)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save problem {problem.problem_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def get_problem_by_id(self, problem_id: ProblemId) -> Optional[Problem]:
        """Get problem by ID."""
        session = self.Session()
        try:
            db_problem = session.query(DBProblem).filter(
                DBProblem.problem_id == str(problem_id.value)
            ).first()
            
            if db_problem:
                return self._map_db_to_domain(db_problem)
            return None
        finally:
            session.close()
    
    async def get_problems_by_subject(self, subject: str) -> List[Problem]:
        """Get problems by subject."""
        session = self.Session()
        try:
            db_problems = session.query(DBProblem).filter(
                DBProblem.subject == subject
            ).all()
            
            return [self._map_db_to_domain(db) for db in db_problems]
        finally:
            session.close()
    
    async def count_problems_by_subject(self, subject: str) -> int:
        """Count problems by subject."""
        session = self.Session()
        try:
            return session.query(DBProblem).filter(
                DBProblem.subject == subject
            ).count()
        finally:
            session.close()
    
    async def initialize_database(self) -> None:
        """Initialize database schema."""
        try:
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            # Create indexes for performance
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_problems_subject 
                    ON problems(subject)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_problems_problem_id 
                    ON problems(problem_id)
                """))
                conn.commit()
            
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise
    
    def _map_domain_to_db(self, domain_problem: Problem) -> DBProblem:
        """Map domain problem to database model."""
        from domain.value_objects import (
            ProblemType, DifficultyLevel, ProblemStatus,
            ExamPart
        )
        
        return DBProblem(
            problem_id=str(domain_problem.problem_id.value),
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
    
    def _map_db_to_domain(self, db_problem: DBProblem) -> Problem:
        """Map database model to domain problem."""
        from domain.value_objects import (
            ProblemType, DifficultyLevel, ProblemStatus,
            ExamPart
        )
        from domain.value_objects.problem_id import ProblemId
        from domain.value_objects.problem_status import ProblemStatusEnum
        
        try:
            problem_type = ProblemType.from_string(db_problem.type) if hasattr(ProblemType, 'from_string') else ProblemType(db_problem.type)
            difficulty_level = DifficultyLevel.from_string(db_problem.difficulty_level) if hasattr(DifficultyLevel, 'from_string') else DifficultyLevel(db_problem.difficulty_level)
            exam_part = db_problem.exam_part
            problem_id = ProblemId(db_problem.problem_id)
            
            # Default status - DRAFT
            status = ProblemStatus(ProblemStatusEnum.DRAFT)
            
            return Problem(
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
    
    async def __aenter__(self) -> "DatabaseServiceAdapter":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        pass
