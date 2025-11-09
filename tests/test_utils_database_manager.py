"""
Тесты для класса DatabaseAdapter.
Проверяют корректность сохранения и извлечения задач и ответов.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from domain.models.problem_schema import Problem
from infrastructure.adapters.database_adapter import DatabaseAdapter


class TestDatabaseAdapter(unittest.TestCase):
    """Тестовый класс для DatabaseAdapter."""

    def setUp(self):
        """Создаёт временный файл БД и инициализирует DatabaseAdapter."""
        self.temp_db_path = Path(tempfile.mktemp(suffix=".db"))
        self.db_manager = DatabaseAdapter(str(self.temp_db_path))
        self.db_manager.initialize_db()

    def tearDown(self):
        """Удаляет временный файл базы данных."""
        if self.temp_db_path.exists():
            self.temp_db_path.unlink()

    def test_save_and_get_problem(self):
        """Проверяет сохранение и извлечение одной задачи."""
        problem = Problem(
            problem_id="task_123",
            subject="math",
            type="short_answer",
            text="Sample text",
            options=[],
            answer="42",
            topics=["KES1"],
            difficulty_level="basic",
            task_number=1,
            exam_part="Part 1",
            max_score=1,
            form_id="",
            source_url="",
            raw_html_path="",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00"
        )

        self.db_manager.save_problems([problem])
        retrieved = self.db_manager.get_problem_by_id("task_123")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.problem_id, problem.problem_id)
        self.assertEqual(retrieved.text, problem.text)
        self.assertEqual(retrieved.answer, problem.answer)

    def test_save_and_get_answer(self):
        """Проверяет сохранение и извлечение ответа."""
        self.db_manager.save_answer("task1", "my_answer", "correct", "test_user")
        user_answer, status = self.db_manager.get_answer_and_status("task1", "test_user")

        self.assertEqual(user_answer, "my_answer")
        self.assertEqual(status, "correct")

    def test_get_answer_not_found(self):
        """Проверяет поведение при запросе несуществующего ответа."""
        user_answer, status = self.db_manager.get_answer_and_status("nonexistent_task", "test_user")
        self.assertIsNone(user_answer)
        self.assertEqual(status, "not_checked")

    def test_get_all_problems(self):
        """Проверяет получение всех задач из БД."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        p1 = Problem(
            problem_id="p1",
            subject="math",
            type="A",
            text="Q1",
            answer="1",
            topics=[],
            difficulty_level="basic",
            task_number=1,
            exam_part="Part 1",
            max_score=1,
            form_id="",
            source_url="",
            raw_html_path="",
            metadata={},
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )
        p2 = Problem(
            problem_id="p2",
            subject="math",
            type="B",
            text="Q2",
            answer="2",
            topics=[],
            difficulty_level="basic",
            task_number=2,
            exam_part="Part 1",
            max_score=1,
            form_id="",
            source_url="",
            raw_html_path="",
            metadata={},
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        self.db_manager.save_problems([p1, p2])
        all_problems = self.db_manager.get_all_problems()

        self.assertEqual(len(all_problems), 2)
        ids = {p.problem_id for p in all_problems}
        self.assertEqual(ids, {"p1", "p2"})
