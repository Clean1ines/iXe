"""
Модуль для управления подключением к SQLite и выполнения CRUD-операций
над задачами и ответами с использованием SQLAlchemy ORM.
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
    Класс для управления базой данных SQLite с использованием SQLAlchemy ORM.

    Инкапсулирует подключение к БД, создание таблиц и основные операции:
    сохранение задач и ответов, получение задач и статусов ответов.
    """

    def __init__(self, db_path: str):
        """Инициализирует менеджер с указанным путём к файлу SQLite.

        Args:
            db_path (str): Путь к файлу базы данных SQLite.
        """
        self.db_path = db_path
        self.engine = sa.create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.debug(f"DatabaseManager initialized with path: {db_path}")

    def initialize_db(self) -> None:
        """Создаёт таблицы в базе данных, если они ещё не существуют."""
        logger.info("Initializing database tables...")
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized (or verified to exist).")
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

    def save_problems(self, problems: List[Problem]) -> None:
        """Сохраняет список задач в базу данных.

        Если задача с таким `problem_id` уже существует, она будет заменена.

        Args:
            problems (List[Problem]): Список Pydantic-моделей задач.
        """
        logger.info(f"Saving {len(problems)} problems to database...")
        try:
            with self.SessionLocal() as session:
                for prob in problems:
                    # Преобразуем Pydantic -> ORM
                    db_problem = DBProblem(
                        problem_id=prob.problem_id,
                        subject=prob.subject,
                        type=prob.type,
                        text=prob.text,
                        options=prob.options,
                        answer=prob.answer,
                        solutions=prob.solutions,
                        topics=prob.topics,
                        skills=prob.skills,
                        # --- Изменено: Заменено 'difficulty' на 'difficulty_level' ---
                        difficulty_level=prob.difficulty_level,
                        # --- Добавлены новые поля ---
                        task_number=prob.task_number,
                        kes_codes=prob.kes_codes,
                        kos_codes=prob.kos_codes,
                        exam_part=prob.exam_part,
                        max_score=prob.max_score,
                        form_id=prob.form_id, # <-- Добавлено: передача form_id
                        # --- /Новые поля ---
                        source_url=prob.source_url,
                        raw_html_path=prob.raw_html_path,
                        created_at=prob.created_at,
                        updated_at=prob.updated_at,
                        metadata_=prob.metadata,
                    )
                    logger.debug(f"Converted problem {prob.problem_id} for saving.")
                    # Замена при конфликте (MERGE-like поведение)
                    session.merge(db_problem)
                    logger.debug(f"Added problem {db_problem.problem_id} to session.")
                session.commit()
            logger.info(f"Successfully saved {len(problems)} problems to database.")
        except Exception as e:
            logger.error(f"Error saving problems to database: {e}", exc_info=True)
            raise

    def save_answer(
        self,
        task_id: str,
        user_answer: str,
        status: str = "not_checked",
        user_id: str = "default_user",
    ) -> None:
        """Сохраняет или обновляет ответ пользователя на задачу.

        Args:
            task_id (str): Идентификатор задачи.
            user_answer (str): Ответ пользователя.
            status (str): Статус проверки ("not_checked", "correct", "incorrect").
            user_id (str): Идентификатор пользователя.
        """
        logger.info(f"Saving answer for task {task_id}, user {user_id}, status {status}. Answer length: {len(user_answer)}")
        try:
            with self.SessionLocal() as session:
                db_answer = DBAnswer(
                    problem_id=task_id,
                    user_id=user_id,
                    user_answer=user_answer,
                    status=status,
                    timestamp=datetime.datetime.now(datetime.UTC),
                )
                session.merge(db_answer)  # Обновляет, если уже существует
                logger.debug(f"Merged/added answer for task {task_id} to session.")
                session.commit()
            logger.info(f"Successfully saved answer for task {task_id}.")
        except Exception as e:
            logger.error(f"Error saving answer for task {task_id} to database: {e}", exc_info=True)
            raise

    def get_answer_and_status(
        self, task_id: str, user_id: str = "default_user"
    ) -> Tuple[Optional[str], str]:
        """Получает ответ и статус по идентификатору задачи.

        Args:
            task_id (str): Идентификатор задачи.
            user_id (str): Идентификатор пользователя.

        Returns:
            Tuple[Optional[str], str]: Кортеж (user_answer, status).
                Если запись не найдена, возвращает (None, "not_checked").
        """
        logger.debug(f"Fetching answer and status for task {task_id}, user {user_id}.")
        try:
            with self.SessionLocal() as session:
                logger.debug(f"Querying database for task {task_id}, user {user_id}.")
                db_answer = (
                    session.query(DBAnswer)
                    .filter_by(problem_id=task_id, user_id=user_id)
                    .first()
                )
                if db_answer:
                    logger.debug(f"Found answer and status ({db_answer.status}) for task {task_id}.")
                    return db_answer.user_answer, db_answer.status
                logger.debug(f"Answer not found for task {task_id}, user {user_id}. Returning default status 'not_checked'.")
                return None, "not_checked"
        except Exception as e:
            logger.error(f"Error fetching answer for task {task_id}, user {user_id}: {e}", exc_info=True)
            raise

    # NEW: Method to get all answers for a specific user and page prefix
    def get_answers_for_user_on_page(
        self, page_name: str, user_id: str = "default_user"
    ) -> Dict[str, Dict[str, str]]:
        """Получает все ответы и статусы для задач на конкретной странице для конкретного пользователя.

        Args:
            page_name (str): Имя страницы (например, 'init', '1', '2').
            user_id (str): Идентификатор пользователя.

        Returns:
            Dict[str, Dict[str, str]]: Словарь, где ключ - problem_id (task_id),
                                       значение - словарь с 'answer' и 'status'.
                                       Возвращает пустой словарь, если ничего не найдено.
        """
        logger.debug(f"Fetching answers for user '{user_id}' on page '{page_name}'.")
        try:
            with self.SessionLocal() as session:
                # Query answers for the specific user
                query = session.query(DBAnswer).filter_by(user_id=user_id)
                all_user_answers = query.all()

                # For now, this method fetches all answers for the user.
                # The page-specific logic must be handled by the caller.
                # The API endpoint must handle the page-specific filtering.
                all_answers = {}
                for db_answer in all_user_answers:
                    all_answers[db_answer.problem_id] = {
                        "answer": db_answer.user_answer,
                        "status": db_answer.status
                    }
                logger.debug(f"Fetched {len(all_answers)} answers for user '{user_id}'.")
                return all_answers

        except Exception as e:
            logger.error(f"Error fetching answers for user '{user_id}' on page '{page_name}': {e}", exc_info=True)
            raise

    # NEW: Method to get all problems for a specific page (example placeholder)
    # This would be needed by the API to know which task_ids belong to a page.
    # It requires the DBProblem table to have a field indicating the page or source URL.
    def get_problem_ids_for_page(self, page_name: str, proj_id: str) -> List[str]:
        """Получает список problem_id (task_id), принадлежащих конкретной странице.

        Args:
            page_name (str): Имя страницы (например, 'init', '1', '2').
            proj_id (str): Идентификатор проекта (subject).

        Returns:
            List[str]: Список problem_id (task_id) для задач на странице.
        """
        logger.debug(f"Fetching problem IDs for page '{page_name}' in project '{proj_id}'.")
        try:
            with self.SessionLocal() as session:
                # Example query assuming source_url contains page information.
                # This is highly dependent on the actual URL structure stored in DBProblem.source_url
                # A more robust approach would be adding a 'page_name' column to DBProblem.
                # For example, if source_url is like ".../questions.php?proj=ID&page=init"
                search_url_pattern = f"%page={page_name}%"
                problems = session.query(DBProblem).filter(
                    DBProblem.source_url.like(search_url_pattern),
                    DBProblem.source_url.like(f"%proj={proj_id}%") # Ensure correct project
                ).all()
                task_ids = [p.problem_id for p in problems]

                # Since source_url might not be reliable for page identification,
                # and DBProblem lacks a 'page_name' field, we cannot reliably implement this
                # without schema changes or other metadata.

                # A common approach would be to add a 'page_name' or 'source_page' field to DBProblem.
                # Example schema change needed:
                # class DBProblem(Base):
                #     ...
                #     source_page: str = sa.Column(sa.String, nullable=False) # e.g., 'init', '1', etc.

                # For now, this method cannot be reliably implemented with the current schema
                # unless there's a way to determine the page from existing fields like source_url.
                # We will return an empty list, indicating this needs further work.
                logger.warning("get_problem_ids_for_page requires a 'page_name' field in DBProblem or reliable source_url parsing.")
                return [] # Placeholder - needs implementation based on schema or URL parsing

        except Exception as e:
            logger.error(f"Error fetching problem IDs for page '{page_name}' in project '{proj_id}': {e}", exc_info=True)
            raise


    def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """Получает задачу по её идентификатору.

        Args:
            problem_id (str): Идентификатор задачи.

        Returns:
            Optional[Problem]: Pydantic-модель задачи или None, если не найдена.
        """
        logger.debug(f"Fetching problem by ID: {problem_id}.")
        try:
            with self.SessionLocal() as session:
                logger.debug(f"Querying database for problem {problem_id}.")
                db_problem = session.query(DBProblem).filter_by(problem_id=problem_id).first()
                if db_problem:
                    logger.debug(f"Found problem {problem_id} in database, converting to Problem schema.")
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
                        # --- Изменено: Заменено 'difficulty' на 'difficulty_level' ---
                        difficulty_level=db_problem.difficulty_level,
                        # --- Добавлены новые поля ---
                        task_number=db_problem.task_number,
                        kes_codes=db_problem.kes_codes,
                        kos_codes=db_problem.kos_codes,
                        exam_part=db_problem.exam_part,
                        max_score=db_problem.max_score,
                        form_id=db_problem.form_id, # <-- Добавлено: передача form_id
                        # --- /Новые поля ---
                        source_url=db_problem.source_url,
                        raw_html_path=db_problem.raw_html_path,
                        created_at=db_problem.created_at,
                        updated_at=db_problem.updated_at,
                        metadata=db_problem.metadata_,
                    )
                logger.debug(f"Problem {problem_id} not found in database.")
                return None
        except Exception as e:
            logger.error(f"Error fetching problem {problem_id}: {e}", exc_info=True)
            raise

    def get_all_problems(self) -> List[Problem]:
        """Получает все задачи из базы данных.

        Returns:
            List[Problem]: Список всех задач в виде Pydantic-моделей.
        """
        logger.debug("Fetching all problems from database.")
        try:
            with self.SessionLocal() as session:
                logger.debug("Querying database for all problems.")
                db_problems = session.query(DBProblem).all()
                logger.info(f"Fetched {len(db_problems)} problems from database, converting to Problem schema.")
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
                        # --- Изменено: Заменено 'difficulty' на 'difficulty_level' ---
                        difficulty_level=p.difficulty_level,
                        # --- Добавлены новые поля ---
                        task_number=p.task_number,
                        kes_codes=p.kes_codes,
                        kos_codes=p.kos_codes,
                        exam_part=p.exam_part,
                        max_score=p.max_score,
                        form_id=p.form_id, # <-- Добавлено: передача form_id
                        # --- /Новые поля ---
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
