import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from models.problem_schema import Problem
from utils.problem_storage import ProblemStorage


class TestProblemStorage(unittest.TestCase):
    def setUp(self):
        # Создаем временный файл для каждого теста
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.jsonl')
        self.temp_file.close()
        self.storage_path = Path(self.temp_file.name)
        self.storage = ProblemStorage(self.storage_path)

    def tearDown(self):
        # Удаляем временный файл после теста
        if self.storage_path.exists():
            os.remove(self.storage_path)

    def test_save_and_load_single_problem(self):
        """Тест сохранения и загрузки одной задачи."""
        problem = Problem(
            problem_id="test_1",
            subject="math",
            type="A",
            text="2+2?",
            answer="4",
            topics=["arithmetic"],
            difficulty="easy",
            created_at=datetime.now()
        )
        self.storage.save_problem(problem)

        loaded_problems = self.storage.load_all_problems()
        self.assertEqual(len(loaded_problems), 1)
        self.assertEqual(loaded_problems[0], problem)

    def test_save_and_load_multiple_problems(self):
        """Тест сохранения и загрузки нескольких задач."""
        problems = [
            Problem(
                problem_id="multi_1",
                subject="math",
                type="A",
                text="2+2?",
                answer="4",
                topics=["arithmetic"],
                difficulty="easy",
                created_at=datetime.now()
            ),
            Problem(
                problem_id="multi_2",
                subject="informatics",
                type="B",
                text="What is RAM?",
                answer="Random Access Memory",
                topics=["hardware"],
                difficulty="medium",
                created_at=datetime.now()
            )
        ]
        self.storage.save_problems(problems)

        loaded_problems = self.storage.load_all_problems()
        self.assertEqual(len(loaded_problems), 2)
        self.assertEqual(loaded_problems, problems)

    def test_get_problem_by_id_found(self):
        """Тест получения задачи по ID, когда она существует."""
        problem1 = Problem(
            problem_id="find_me",
            subject="russian",
            type="C",
            text="Decline the noun 'стол'.",
            answer="стол, стола, столу...",
            topics=["grammar"],
            difficulty="hard",
            created_at=datetime.now()
        )
        problem2 = Problem(
            problem_id="ignore_me",
            subject="history",
            type="A",
            text="When did WWII end?",
            answer="1945",
            topics=["20th_century"],
            difficulty="medium",
            created_at=datetime.now()
        )
        self.storage.save_problems([problem1, problem2])

        found_problem = self.storage.get_problem_by_id("find_me")
        self.assertIsNotNone(found_problem)
        self.assertEqual(found_problem, problem1)

    def test_get_problem_by_id_not_found(self):
        """Тест получения задачи по ID, когда она не существует."""
        problem = Problem(
            problem_id="existing_id",
            subject="math",
            type="A",
            text="1+1?",
            answer="2",
            topics=["arithmetic"],
            difficulty="easy",
            created_at=datetime.now()
        )
        self.storage.save_problem(problem)

        found_problem = self.storage.get_problem_by_id("nonexistent_id")
        self.assertIsNone(found_problem)

    def test_load_empty_file(self):
        """Тест загрузки из пустого файла."""
        # Убедимся, что файл существует и пуст
        self.storage_path.touch(exist_ok=True)
        self.assertTrue(self.storage_path.stat().st_size == 0)

        loaded_problems = self.storage.load_all_problems()
        self.assertEqual(loaded_problems, [])
