"""
Unit tests for the ProblemBuilder class.
"""
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from models.problem_builder import ProblemBuilder
from models.problem_schema import Problem


class TestProblemBuilder(unittest.TestCase):
    """
    Test cases for the ProblemBuilder class.
    """

    def setUp(self):
        """
        Set up the ProblemBuilder instance for tests.
        """
        self.builder = ProblemBuilder()

    def test_build_creates_correct_problem(self):
        """
        Test that the build method creates a Problem instance with correct attributes.
        """
        # Prepare test data
        problem_id = "init_0_40B442"
        subject = "mathematics"
        type_str = "A"
        text = "Solve the equation $x^2 = 4$."
        topics = ["algebra.equations", "math.basic"]
        difficulty_level = "easy"
        source_url = "https://fipi.ru/ege/123  "
        metadata = {"original_format": "html", "parsed_by": "v1.0"}
        raw_html_path_input = Path("/tmp/raw.html")
        # Ожидаем, что builder конвертирует Path в строку
        expected_raw_html_path_str = str(raw_html_path_input)

        # Prepare optional test data
        options = ["Option A", "Option B"]
        answer = "Correct Answer"
        solutions = [{"id": "sol_1", "text": "A good solution.", "author": "Alice"}]
        skills = ["skill1", "skill2"]

        # Build the problem
        problem = self.builder.build(
            problem_id=problem_id,
            subject=subject,
            type_str=type_str,
            text=text,
            topics=topics,
            difficulty_level=difficulty_level,
            source_url=source_url,
            metadata=metadata,
            raw_html_path=raw_html_path_input,
            # --- Передаём новые аргументы ---
            options=options,
            answer=answer,
            solutions=solutions,
            skills=skills,
            updated_at=None # Явно передаём None для нового поля
            # --------------------------------
        )

        # Assertions
        self.assertIsInstance(problem, Problem)
        self.assertEqual(problem.problem_id, problem_id)
        self.assertEqual(problem.subject, subject)
        self.assertEqual(problem.type, type_str)
        self.assertEqual(problem.text, text)
        self.assertEqual(problem.topics, topics)
        self.assertEqual(problem.difficulty_level, difficulty_level)
        self.assertEqual(problem.source_url, source_url)
        self.assertEqual(problem.metadata, metadata)
        # Проверяем, что в модели сохранена строка, и она равна ожидаемой строке
        self.assertEqual(problem.raw_html_path, expected_raw_html_path_str)
        # Убедимся, что тип в модели - строка
        self.assertIsInstance(problem.raw_html_path, str)

        # --- Проверяем новые/обновлённые поля ---
        self.assertEqual(problem.options, options)
        self.assertEqual(problem.answer, answer)
        self.assertEqual(problem.solutions, solutions)
        self.assertEqual(problem.skills, skills)
        self.assertIsNone(problem.updated_at) # Проверяем, что переданный None сохранился
        # ---------------------------------------


        # Check created_at is a datetime and is recent
        self.assertIsInstance(problem.created_at, datetime)
        now = datetime.now()
        time_threshold = timedelta(seconds=5)
        self.assertLess(problem.created_at, now + time_threshold)
        self.assertGreater(problem.created_at, now - time_threshold)

    def test_build_with_none_raw_html_path(self):
        """
        Test building a Problem with raw_html_path set to None.
        """
        problem_id = "test_none_path"
        subject = "physics"
        type_str = "task_5"
        text = "Calculate the force."
        topics = ["physics.mechanics"]
        difficulty_level = "medium"
        source_url = "https://fipi.ru/ege/456  "
        metadata = {}

        # Build with new optional arguments explicitly set to None/default
        problem = self.builder.build(
            problem_id=problem_id,
            subject=subject,
            type_str=type_str,
            text=text,
            topics=topics,
            difficulty_level=difficulty_level,
            source_url=source_url,
            metadata=metadata,
            raw_html_path=None,
            # --- Явно передаём остальные аргументы ---
            options=None,
            answer="placeholder_answer", # Используем значение по умолчанию из build
            solutions=None,
            skills=None,
            updated_at=None
            # --------------------------------------
        )

        self.assertIsInstance(problem, Problem)
        self.assertIsNone(problem.raw_html_path)
        self.assertEqual(problem.problem_id, problem_id)
        self.assertEqual(problem.subject, subject)
        self.assertEqual(problem.type, type_str)
        self.assertEqual(problem.text, text)
        self.assertEqual(problem.topics, topics)
        self.assertEqual(problem.difficulty_level, difficulty_level)
        self.assertEqual(problem.source_url, source_url)
        self.assertEqual(problem.metadata, metadata)

        # --- Проверяем, что все новые поля тоже None ---
        self.assertIsNone(problem.options)
        self.assertEqual(problem.answer, "placeholder_answer")
        self.assertIsNone(problem.solutions)
        self.assertIsNone(problem.skills)
        self.assertIsNone(problem.updated_at)
        # ------------------------------------------------


        # Check created_at is a datetime and is recent
        self.assertIsInstance(problem.created_at, datetime)
        now = datetime.now()
        time_threshold = timedelta(seconds=5)
        self.assertLess(problem.created_at, now + time_threshold)
        self.assertGreater(problem.created_at, now - time_threshold)

    def test_build_with_empty_metadata(self):
        """
        Test building a Problem with an empty metadata dictionary.
        """
        problem_id = "test_empty_meta"
        subject = "chemistry"
        type_str = "B"
        text = "Balance the equation."
        topics = ["chemistry.equations"]
        difficulty_level = "hard"
        source_url = "https://fipi.ru/ege/789  "
        metadata = {}
        raw_html_path_input = Path("/tmp/chem.html")
        expected_raw_html_path_str = str(raw_html_path_input)

        # Build with new optional arguments explicitly set to None/default
        problem = self.builder.build(
            problem_id=problem_id,
            subject=subject,
            type_str=type_str,
            text=text,
            topics=topics,
            difficulty_level=difficulty_level,
            source_url=source_url,
            metadata=metadata,
            raw_html_path=raw_html_path_input,
            # --- Явно передаём остальные аргументы ---
            options=None,
            answer="placeholder_answer",
            solutions=None,
            skills=None,
            updated_at=None
            # --------------------------------------
        )

        self.assertIsInstance(problem, Problem)
        # Проверяем строку
        self.assertEqual(problem.raw_html_path, expected_raw_html_path_str)
        self.assertIsInstance(problem.raw_html_path, str)
        self.assertEqual(problem.metadata, {})
        self.assertEqual(problem.problem_id, problem_id)
        self.assertEqual(problem.subject, subject)
        self.assertEqual(problem.type, type_str)
        self.assertEqual(problem.text, text)
        self.assertEqual(problem.topics, topics)
        self.assertEqual(problem.difficulty_level, difficulty_level)
        self.assertEqual(problem.source_url, source_url)
        # self.assertEqual(problem.raw_html_path, raw_html_path) # Старая строка, вызывающая ошибку

        # --- Проверяем, что все новые поля тоже None ---
        self.assertIsNone(problem.options)
        self.assertEqual(problem.answer, "placeholder_answer")
        self.assertIsNone(problem.solutions)
        self.assertIsNone(problem.skills)
        self.assertIsNone(problem.updated_at)
        # ------------------------------------------------


        # Check created_at is a datetime and is recent
        self.assertIsInstance(problem.created_at, datetime)
        now = datetime.now()
        time_threshold = timedelta(seconds=5)
        self.assertLess(problem.created_at, now + time_threshold)
        self.assertGreater(problem.created_at, now - time_threshold)


if __name__ == '__main__':
    unittest.main()
