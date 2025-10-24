"""
Модуль для управления подключением к SQLite и выполнения CRUD-операций
над задачами и ответами с использованием SQLAlchemy ORM.
"""

import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from models.database_models import Base, DBProblem, DBAnswer
from models.problem_schema import Problem


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

    def initialize_db(self) -> None:
        """Создаёт таблицы в базе данных, если они ещё не существуют."""
        Base.metadata.create_all(self.engine)

    def save_problems(self, problems: List[Problem]) -> None:
        """Сохраняет список задач в базу данных.

        Если задача с таким `problem_id` уже существует, она будет заменена.

        Args:
            problems (List[Problem]): Список Pydantic-моделей задач.
        """
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
                # Замена при конфликте (MERGE-like поведение)
                session.merge(db_problem)
            session.commit()

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
        with self.SessionLocal() as session:
            db_answer = DBAnswer(
                problem_id=task_id,
                user_id=user_id,
                user_answer=user_answer,
                status=status,
                timestamp=datetime.datetime.now(datetime.UTC),
            )
            session.merge(db_answer)  # Обновляет, если уже существует
            session.commit()

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
        with self.SessionLocal() as session:
            db_answer = (
                session.query(DBAnswer)
                .filter_by(problem_id=task_id, user_id=user_id)
                .first()
            )
            if db_answer:
                return db_answer.user_answer, db_answer.status
            return None, "not_checked"

    def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """Получает задачу по её идентификатору.

        Args:
            problem_id (str): Идентификатор задачи.

        Returns:
            Optional[Problem]: Pydantic-модель задачи или None, если не найдена.
        """
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
                    difficulty=db_problem.difficulty,
                    source_url=db_problem.source_url,
                    raw_html_path=db_problem.raw_html_path,
                    created_at=db_problem.created_at,
                    updated_at=db_problem.updated_at,
                    metadata=db_problem.metadata_,
                )
            return None

    def get_all_problems(self) -> List[Problem]:
        """Получает все задачи из базы данных.

        Returns:
            List[Problem]: Список всех задач в виде Pydantic-моделей.
        """
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
                    difficulty=p.difficulty,
                    source_url=p.source_url,
                    raw_html_path=p.raw_html_path,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    metadata=p.metadata_,
                )
                for p in db_problems
            ]
