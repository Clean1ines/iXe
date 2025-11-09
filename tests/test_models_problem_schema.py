import unittest
from domain.models.problem_schema import Problem

class TestProblemSchema(unittest.TestCase):
    def test_valid_problem_creation(self):
        data = {
            "problem_id": "test_123",
            "subject": "math",
            "type": "multiple_choice",
            "text": "What is 2+2?",
            "options": ["3", "4", "5"],
            "answer": "4",
            "topics": ["KES1", "KES2"],
            "difficulty_level": "basic",
            "task_number": 1,
            "exam_part": "Part 1",
            "max_score": 1,
            "form_id": "form123",
            "source_url": "http://example.com",
            "raw_html_path": "/path/to/html",
            "metadata": {"key": "value"}
        }
        problem = Problem(**data)
        self.assertEqual(problem.problem_id, "test_123")

    def test_problem_with_minimal_fields(self):
        data = {
            "problem_id": "minimal_456",
            "subject": "math",
            "type": "short_answer",
            "text": "Solve for x.",
            "options": [],
            "answer": "42",
            "topics": ["KES3"],
            "difficulty_level": "basic",
            "task_number": 2,
            "exam_part": "Part 2",
            "max_score": 2,
            "form_id": "",
            "source_url": "",
            "raw_html_path": "",
            "metadata": {}
        }
        problem = Problem(**data)
        self.assertEqual(problem.problem_id, "minimal_456")

    def test_problem_validation_error(self):
        with self.assertRaises(ValueError):
            Problem(problem_id="bad", subject="math")  # missing required fields
