"""
Тесты для SQLAlchemy ORM-моделей задач и ответов.
Проверяют корректность создания и сохранения объектов в памяти (in-memory SQLite).
"""

import unittest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.models.database_models import Base, DBProblem, DBAnswer


class TestDatabaseModels(unittest.TestCase):
    """Тестовый класс для проверки ORM-моделей."""

    def setUp(self):
        """Создаёт in-memory SQLite базу и таблицы перед каждым тестом."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()

    def tearDown(self):
        """Закрывает сессию и освобождает ресурсы после каждого теста."""
        self.session.close()
        self.engine.dispose()

    def test_create_problem_and_answer(self):
        """Проверяет создание и сохранение задачи и связанного с ней ответа."""
        # Подготовка данных
        now = datetime.datetime.now(datetime.UTC)
        problem = DBProblem(
            problem_id="init_0_40B442",
            subject="mathematics",
            type="task_1",
            text="Решите уравнение $x^2 = 4$.",
            options=None,
            answer="2",
            solutions=None,
            topics=["algebra.equations"],
            skills=["solve_linear"],
            difficulty="easy",
            source_url="https://fipi.ru/example",
            raw_html_path=None,
            created_at=now,
            updated_at=None,
            metadata_=None,
        )

        answer = DBAnswer(
            problem_id=problem.problem_id,
            user_answer="2",
            status="correct",
            timestamp=now,
        )

        # Сохранение в БД
        self.session.add(problem)
        self.session.add(answer)
        self.session.commit()

        # Проверка: объекты должны быть в БД
        retrieved_problem = self.session.query(DBProblem).filter_by(problem_id="init_0_40B442").first()
        retrieved_answer = self.session.query(DBAnswer).filter_by(problem_id="init_0_40B442").first()

        self.assertIsNotNone(retrieved_problem)
        self.assertEqual(retrieved_problem.subject, "mathematics")
        self.assertEqual(retrieved_problem.text, "Решите уравнение $x^2 = 4$.")

        self.assertIsNotNone(retrieved_answer)
        self.assertEqual(retrieved_answer.user_answer, "2")
        self.assertEqual(retrieved_answer.status, "correct")
        self.assertEqual(retrieved_answer.problem_id, "init_0_40B442")

        # Проверка связи
        self.assertEqual(retrieved_answer.problem.problem_id, "init_0_40B442")
