"""
Module for managing database operations with support for different backends (SQLite, Supabase).
Provides an abstraction layer for saving and retrieving problems and answers.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Type, TypeVar, Any, Dict

from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from common.models.problem_schema import Problem
from common.models.database_models import Base, DBProblem, DBAnswer

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)

class DatabaseBackend(ABC):
    """Abstract base class for database backends."""
    
    @abstractmethod
    async def save_problems(self, problems: List[Problem]) -> List[str]:
        """Save a list of problems to the database."""
        pass
    
    @abstractmethod
    async def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """Retrieve a problem by its ID."""
        pass

    @abstractmethod
    async def save_answer(self, problem_id: str, user_id: str, user_answer: str, status: str) -> None:
        """Save a user's answer to a problem."""
        pass

    @abstractmethod
    async def get_answers_for_problem(self, problem_id: str, user_id: Optional[str] = None) -> List[DBAnswer]:
        """Retrieve answers for a specific problem, optionally filtered by user."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection."""
        pass


class SQLDatabaseBackend(DatabaseBackend):
    """Database backend implementation for SQLite using SQLAlchemy."""

    def __init__(self, database_url: str):
        """
        Initialize the SQLite backend.

        Args:
            database_url: SQLAlchemy-compatible database URL (e.g., "sqlite+aiosqlite:///data/fipi_data.db").
        """
        self.database_url = database_url
        # Async engine for SQLAlchemy operations
        self.async_engine = create_async_engine(self.database_url)
        # Async session maker
        self.async_session = sessionmaker(self.async_engine, class_=AsyncSession, expire_on_commit=False)
        logger.info(f"SQLDatabaseBackend initialized with URL: {database_url}")

    async def save_problems(self, problems: List[Problem]) -> List[str]:
        """
        Save a list of Pydantic Problem models to the database as DBProblem ORM objects.

        Args:
            problems: List of Problem models to save.

        Returns:
            List of problem IDs that were saved.
        """
        saved_ids = []
        async with self.async_session() as session:
            try:
                for problem in problems:
                    # Convert Pydantic Problem to SQLAlchemy DBProblem
                    # Handle optional fields explicitly
                    db_problem = DBProblem(
                        problem_id=problem.problem_id,
                        subject=problem.subject,
                        type=problem.type,
                        text=problem.text,
                        options=problem.options,
                        answer=problem.answer,
                        topics=problem.kes_codes,  # Mapping kes_codes to topics for ORM compatibility
                        kes_codes=problem.kes_codes,
                        kos_codes=problem.kos_codes,
                        difficulty_level=problem.difficulty_level,
                        task_number=problem.task_number,
                        exam_part=problem.exam_part,
                        max_score=problem.max_score,
                        form_id=problem.form_id,
                        source_url=problem.source_url,
                        raw_html_path=problem.raw_html_path,
                        created_at=problem.created_at,
                        updated_at=problem.updated_at,
                        # Note: metadata might need special handling if it contains non-serializable types
                        # For now, assuming it's a simple dict that can be stored as JSON by SQLAlchemy
                        metadata=problem.metadata
                    )
                    
                    session.add(db_problem)
                    saved_ids.append(problem.problem_id)
                
                await session.commit()
                logger.info(f"Successfully saved {len(problems)} problems to database.")
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error while saving problems: {e}")
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while saving problems: {e}")
                raise
        
        return saved_ids

    async def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """
        Retrieve a Pydantic Problem model by its ID from the database.

        Args:
            problem_id: The ID of the problem to retrieve.

        Returns:
            The Problem model if found, otherwise None.
        """
        async with self.async_session() as session:
            try:
                # Use SQLAlchemy's select to query DBProblem
                stmt = select(DBProblem).where(DBProblem.problem_id == problem_id)
                result = await session.execute(stmt)
                db_problem = result.scalar_one_or_none()
                
                if db_problem:
                    # Convert SQLAlchemy DBProblem back to Pydantic Problem
                    # This assumes a compatible structure or a conversion helper
                    # For now, assuming direct mapping is possible via dict
                    from common.utils.model_adapter import db_problem_to_problem
                    return db_problem_to_problem(db_problem)
                
                return None
            
            except SQLAlchemyError as e:
                logger.error(f"Database error while getting problem {problem_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error while getting problem {problem_id}: {e}")
                raise

    async def save_answer(self, problem_id: str, user_id: str, user_answer: str, status: str = "not_checked") -> None:
        """
        Save a user's answer to a specific problem.

        Args:
            problem_id: The ID of the problem being answered.
            user_id: The ID of the user providing the answer.
            user_answer: The text of the user's answer.
            status: The initial status of the answer (default: "not_checked").
        """
        async with self.async_session() as session:
            try:
                db_answer = DBAnswer(
                    problem_id=problem_id,
                    user_id=user_id,
                    user_answer=user_answer,
                    status=status
                )
                session.add(db_answer)
                await session.commit()
                logger.debug(f"Saved answer for problem {problem_id} and user {user_id}.")
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error while saving answer for problem {problem_id}: {e}")
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while saving answer for problem {problem_id}: {e}")
                raise

    async def get_answers_for_problem(self, problem_id: str, user_id: Optional[str] = None) -> List[DBAnswer]:
        """
        Retrieve answers for a specific problem, optionally filtered by user.

        Args:
            problem_id: The ID of the problem.
            user_id: Optional user ID to filter answers.

        Returns:
            List of DBAnswer objects.
        """
        async with self.async_session() as session:
            try:
                stmt = select(DBAnswer).where(DBAnswer.problem_id == problem_id)
                if user_id:
                    stmt = stmt.where(DBAnswer.user_id == user_id)
                
                result = await session.execute(stmt)
                answers = result.scalars().all()
                return answers
            
            except SQLAlchemyError as e:
                logger.error(f"Database error while getting answers for problem {problem_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error while getting answers for problem {problem_id}: {e}")
                raise

    async def close(self) -> None:
        """Close the database engine."""
        await self.async_engine.dispose()
        logger.info("SQLDatabaseBackend closed.")


class DatabaseManager:
    """
    High-level manager for database operations, abstracting the backend implementation.
    Supports switching between different database backends like SQLite and Supabase.
    """
    
    def __init__(self, backend: DatabaseBackend):
        """
        Initialize the manager with a specific backend.

        Args:
            backend: An instance of a DatabaseBackend implementation.
        """
        self.backend = backend
        logger.debug(f"DatabaseManager initialized with backend: {type(backend).__name__}")

    async def save_problems(self, problems: List[Problem]) -> List[str]:
        """Save a list of problems using the configured backend."""
        return await self.backend.save_problems(problems)

    async def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """Retrieve a problem by ID using the configured backend."""
        return await self.backend.get_problem_by_id(problem_id)

    async def save_answer(self, problem_id: str, user_id: str, user_answer: str, status: str = "not_checked") -> None:
        """Save a user's answer using the configured backend."""
        await self.backend.save_answer(problem_id, user_id, user_answer, status)

    async def get_answers_for_problem(self, problem_id: str, user_id: Optional[str] = None) -> List[DBAnswer]:
        """Retrieve answers for a problem using the configured backend."""
        return await self.backend.get_answers_for_problem(problem_id, user_id)

    async def close(self) -> None:
        """Close the underlying database backend."""
        await self.backend.close()

