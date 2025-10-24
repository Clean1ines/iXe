"""
Тесты для класса DatabaseManager.
Проверяют корректность сохранения и извлечения задач и ответов.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from models.problem_schema import Problem
from utils.database_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Тестовый класс для DatabaseManager."""

    def setUp(self):
        """Создаёт временный файл БД и инициализирует DatabaseManager."""
        self.temp_db_path = Path(tempfile.mktemp(suffix=".db"))
        self.db_manager = DatabaseManager(str(self.temp_db_path))
        self.db_manager.initialize_db()

    def tearDown(self):
        """Удаляет временный файл базы данных."""
        if self.temp_db_path.exists():
            self.temp_db_path.unlink()

    def test_save_and_get_problem(self):
        """Проверяет сохранение и извлечение одной задачи."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC
        problem = Problem(
            problem_id="task_123",
            subject="mathematics",
            type="task_1",
            text="Решите уравнение.",
            options=None,
            answer="42",
            solutions=None,
            topics=["algebra"],
            skills=["solve"],
            difficulty="medium",
            source_url="https://fipi.ru/task_123",
            raw_html_path=None,
            created_at=now,
            updated_at=None,
            metadata=None,
        )

        self.db_manager.save_problems([problem])
        retrieved = self.db_manager.get_problem_by_id("task_123")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.problem_id, problem.problem_id)
        self.assertEqual(retrieved.text, problem.text)
        self.assertEqual(retrieved.answer, problem.answer)

    def test_save_and_get_answer(self):
        """Проверяет сохранение и извлечение ответа."""
        self.db_manager.save_answer("task1", "my_answer", "correct")
        user_answer, status = self.db_manager.get_answer_and_status("task1")

        self.assertEqual(user_answer, "my_answer")
        self.assertEqual(status, "correct")

    def test_get_answer_not_found(self):
        """Проверяет поведение при запросе несуществующего ответа."""
        user_answer, status = self.db_manager.get_answer_and_status("nonexistent_task")
        self.assertIsNone(user_answer)
        self.assertEqual(status, "not_checked")

    def test_get_all_problems(self):
        """Проверяет получение всех задач из БД."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        p1 = Problem(
            difficulty="easy",
            problem_id="p1", subject="math", type="A", text="Q1", answer="1",
            topics=[], created_at=now
        )
        p2 = Problem(
            difficulty="easy",
            problem_id="p2", subject="math", type="B", text="Q2", answer="2",
            topics=[], created_at=now
        )

        self.db_manager.save_problems([p1, p2])
        all_problems = self.db_manager.get_all_problems()

        self.assertEqual(len(all_problems), 2)
        ids = {p.problem_id for p in all_problems}
        self.assertEqual(ids, {"p1", "p2"})
