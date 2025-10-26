import unittest
from datetime import datetime
from pydantic import ValidationError
from models.problem_schema import Problem


class TestProblemSchema(unittest.TestCase):
    def test_valid_problem_creation(self):
        """Тест создания задачи со всеми полями."""
        data = {
            "problem_id": "test_123",
            "subject": "mathematics",
            "type": "A",
            "text": "Solve for x.",
            "options": ["1", "2", "3", "4"],
            "answer": "2",
            "solutions": [{"id": "sol_1", "text": "Solution text", "author": "author1"}],
            "topics": ["algebra.equations"],
            "skills": ["solve_equation"],
            "difficulty": "medium",
            "source_url": "http://fipi.ru/test_123",
            "raw_html_path": "/path/to/html",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "metadata": {"key": "value"}
        }
        problem = Problem(**data)
        self.assertEqual(problem.problem_id, "test_123")
        self.assertEqual(problem.subject, "mathematics")
        self.assertEqual(problem.text, "Solve for x.")
        self.assertEqual(problem.options, ["1", "2", "3", "4"])
        self.assertEqual(problem.answer, "2")
        self.assertEqual(problem.solutions, [{"id": "sol_1", "text": "Solution text", "author": "author1"}])
        self.assertEqual(problem.difficulty, "medium")
        self.assertEqual(problem.source_url, "http://fipi.ru/test_123")
        self.assertEqual(problem.topics, ["algebra.equations"])
        self.assertEqual(problem.skills, ["solve_equation"])
        self.assertIsNotNone(problem.created_at)
        self.assertIsNotNone(problem.updated_at)
        self.assertEqual(problem.metadata, {"key": "value"})

    def test_problem_with_minimal_fields(self):
        """Тест создания задачи только с обязательными полями."""
        data = {
            "problem_id": "minimal_456",
            "subject": "informatics",
            "type": "B",
            "text": "What is an algorithm?",
            "answer": "A step-by-step procedure",
            "topics": [],
            "difficulty": "easy",
            "created_at": datetime.now()
        }
        problem = Problem(**data)
        self.assertEqual(problem.problem_id, "minimal_456")
        self.assertEqual(problem.subject, "informatics")
        self.assertEqual(problem.text, "What is an algorithm?")
        self.assertEqual(problem.answer, "A step-by-step procedure")
        self.assertEqual(problem.topics, [])
        self.assertEqual(problem.difficulty, "easy")
        self.assertIsNotNone(problem.created_at)
        # Проверяем, что опциональные поля по умолчанию None или []
        self.assertIsNone(problem.options)
        self.assertIsNone(problem.solutions)
        self.assertIsNone(problem.skills)
        self.assertIsNone(problem.source_url)
        self.assertIsNone(problem.raw_html_path)
        self.assertIsNone(problem.updated_at)
        self.assertIsNone(problem.metadata)

    def test_problem_validation_error(self):
        """Тест ошибки валидации при отсутствии обязательного поля problem_id."""
        data = {
            # "problem_id": "missing",  # Пропущено обязательное поле
            "subject": "russian",
            "type": "C",
            "text": "Write an essay.",
            "answer": "Essay text",
            "topics": ["writing.essay"],
            "difficulty": "hard",
            "created_at": datetime.now()
        }
        with self.assertRaises(ValidationError):
            Problem(**data)
