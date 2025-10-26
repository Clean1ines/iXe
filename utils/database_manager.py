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
                        difficulty=prob.difficulty,
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

                # Filter answers based on the page name.
                # Since problem_id is the task_id (e.g., '40B442'), we need to determine
                # if this task_id belongs to the given page_name.
                # This requires fetching the corresponding DBProblem records or having
                # a way to map task_id to page_name.
                # For now, let's assume we need to filter based on a convention
                # where task_id might contain the page name as a prefix or is somehow
                # determinable from the context provided by the page rendering process.
                # However, since task_id itself (like '40B442') does not inherently
                # contain the page name (like 'init'), this is a complex lookup.
                # A better approach might be to pass the list of task_ids expected
                # for the page from the renderer and filter against that.

                # For this implementation, we'll assume that the page_name is used
                # to determine the set of task_ids that belong to it elsewhere,
                # and this function fetches answers for *any* task_id for the user.
                # The filtering by page context must happen in the caller (e.g., in the API).
                # However, if we *could* filter by page_name here, it would require
                # a join with the problems table or a different schema design.
                # As per the current schema, problem_id in answers table is just task_id.
                # We will return all answers for the user, and the API caller
                # is responsible for further filtering or association with page content.
                # This is suboptimal but reflects the current schema limitations for
                # direct page -> problem_id mapping.

                # A potential future improvement would be to add a 'page_name' column
                # to the DBProblem table, allowing a join here.
                # For now, this method fetches all answers for the user.
                # The caller (e.g., get_initial_state_for_page in answer_api.py)
                # should manage the association with the page's specific task IDs.

                # This implementation returns ALL user answers.
                # The API endpoint must handle the page-specific filtering.
                # If we had a way to link task_id to page_name (e.g., by fetching
                # all problems for a page first), we could do the filtering here.
                # Let's assume the caller provides the list of relevant task_ids.

                # Alternative approach: Fetch all answers for the user
                all_answers = {}
                for db_answer in all_user_answers:
                    # This does not filter by page_name directly.
                    # The page-specific logic must be handled by the caller.
                    # For now, we return all answers for the user.
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
    # Since the current schema for DBProblem doesn't explicitly store the page name,
    # we might need to infer it from the source_url or another field, or add a field.
    # For now, this is a conceptual placeholder if source_url contains page info.
    def get_problem_ids_for_page(self, page_name: str, proj_id: str) -> List[str]:
        """Получает список problem_id (task_id), принадлежащих конкретной странице.

        Args:
            page_name (str): Имя страницы (например, 'init', '1', '2').
            proj_id (str): Идентификатор проекта (subject).

        Returns:
            List[str]: Список problem_id (task_id) для задач на странице.
        """
        # This is a conceptual example assuming source_url contains page information.
        # In practice, DBProblem might need a 'page_name' field for direct lookup.
        # For now, let's assume source_url contains the page identifier.
        logger.debug(f"Fetching problem IDs for page '{page_name}' in project '{proj_id}'.")
        try:
            with self.SessionLocal() as session:
                # Example query assuming source_url contains '?page=init' or similar
                # This is highly dependent on the actual URL structure stored in DBProblem.source_url
                # A more robust approach would be adding a 'page_name' column to DBProblem.
                # For example, if source_url is like ".../questions.php?proj=ID&page=init"
                # We could filter like this:
                # search_url_pattern = f"%page={page_name}%" # Be careful with SQL LIKE wildcards
                # problems = session.query(DBProblem).filter(
                #     DBProblem.source_url.like(search_url_pattern),
                #     DBProblem.source_url.like(f"%proj={proj_id}%") # Ensure correct project
                # ).all()
                # task_ids = [p.problem_id for p in problems]

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
                        difficulty=db_problem.difficulty,
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
                        difficulty=p.difficulty,
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

