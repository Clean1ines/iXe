"""
Тесты для api/core_api.py с использованием TestClient.
"""
import unittest
import tempfile
import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from api.core_api import create_core_app
from utils.database_manager import DatabaseManager
from models.problem_schema import Problem
from datetime import datetime


class TestCoreAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Создаём временную базу данных
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix='.db')
        os.close(cls.temp_db_fd)  # Закрываем дескриптор, FastAPI откроет его сам

        cls.db_manager = DatabaseManager(cls.temp_db_path)
        cls.db_manager.initialize_db()

        # Добавляем тестовые данные в БД
        test_problem_1 = Problem(
            problem_id="test_001",
            subject="mathematics",
            type="A",
            text="What is 2+2?",
            options=["1", "2", "3", "4"],
            answer="4",
            solutions=None,
            topics=["arithmetic"],
            skills=["addition"],
            difficulty="easy",
            source_url="http://example.com/problem/001",
            raw_html_path=None,
            created_at=datetime.now(),
            updated_at=None,
            metadata=None
        )
        test_problem_2 = Problem(
            problem_id="test_002",
            subject="russian",
            type="B",
            text="Напишите слово 'мир'.",
            options=None,
            answer="мир",
            solutions=None,
            topics=["orthography"],
            skills=["spelling"],
            difficulty="medium",
            source_url="http://example.com/problem/002",
            raw_html_path=None,
            created_at=datetime.now(),
            updated_at=None,
            metadata=None
        )
        cls.db_manager.save_problems([test_problem_1, test_problem_2])

        # Создаём приложение и клиент
        cls.app = create_core_app(cls.db_manager)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        # Удаляем временный файл базы данных
        os.unlink(cls.temp_db_path)

    def test_root_endpoint(self):
        """Тестирует корневой эндпоинт."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, {"message": "FIPI Core API (MVP) is running"})

    def test_post_quiz_daily_start(self):
        """Тестирует эндпоинт запуска ежедневного квиза."""
        payload = {"page_name": "test_page"}
        response = self.client.post("/quiz/daily/start", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Проверяем структуру ответа
        self.assertIn("quiz_id", data)
        self.assertIn("items", data)
        self.assertIsInstance(data["items"], list)
        self.assertTrue(len(data["items"]) > 0)  # Должен быть хотя бы один элемент, так как БД не пуста
        self.assertTrue(len(data["quiz_id"]) > 0)  # ID квиза не должен быть пустым

        # Проверяем структуру первого элемента списка items
        first_item = data["items"][0]
        self.assertIn("problem_id", first_item)
        self.assertIn("subject", first_item)
        self.assertIn("topic", first_item)
        self.assertIn("prompt", first_item)
        self.assertIn("choices_or_input_type", first_item)

    def test_post_quiz_finish(self):
        """Тестирует эндпоинт завершения квиза."""
        quiz_id = "test_quiz_123"
        payload = {
            "results": [
                {"problem_id": "p1", "user_answer": "ans1", "time_spent": 10},
                {"problem_id": "p2", "user_answer": "ans2", "time_spent": 15}
            ]
        }
        response = self.client.post(f"/quiz/{quiz_id}/finish", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Проверяем структуру ответа
        self.assertIn("score", data)
        self.assertIn("per_topic_accuracy", data)
        self.assertIn("recommended_actions", data)

        # Проверяем типы значений
        self.assertIsInstance(data["score"], float)
        self.assertIsInstance(data["per_topic_accuracy"], dict)
        self.assertIsInstance(data["recommended_actions"], list)

    def test_post_answer(self):
        """Тестирует эндпоинт проверки ответа."""
        payload = {"problem_id": "p1", "user_answer": "test_answer"}
        response = self.client.post("/answer", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Проверяем структуру ответа
        self.assertIn("verdict", data)
        self.assertIn("score_float", data)
        self.assertIn("short_hint", data)
        self.assertIn("evidence", data)
        self.assertIn("deep_explanation_id", data)

        # Проверяем типы значений
        self.assertIsInstance(data["verdict"], str)
        self.assertIsInstance(data["score_float"], float)
        self.assertIsInstance(data["short_hint"], str)
        self.assertIsInstance(data["evidence"], list)
        # deep_explanation_id может быть None или строкой
        self.assertTrue(data["deep_explanation_id"] is None or isinstance(data["deep_explanation_id"], str))

        # Проверяем, что verdict - один из ожидаемых
        self.assertIn(data["verdict"], ["correct", "incorrect", "insufficient_data"])

    def test_post_plan_generate(self):
        """Тестирует эндпоинт генерации плана."""
        payload = {
            "user_id": "u1",
            "target_date": "2025-12-01",
            "time_per_week_hours": 5
        }
        response = self.client.post("/plan/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Проверяем структуру ответа
        self.assertIn("plan_id", data)
        self.assertIn("weeks", data)

        # Проверяем типы значений
        self.assertIsInstance(data["plan_id"], str)
        self.assertIsInstance(data["weeks"], list)

        # Проверяем структуру первого элемента списка weeks, если он есть
        if data["weeks"]:
            first_week = data["weeks"][0]
            self.assertIn("week_number", first_week)
            self.assertIn("focus_topics", first_week)
            self.assertIn("daily_tasks", first_week)


if __name__ == '__main__':
    unittest.main()

