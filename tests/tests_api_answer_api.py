# tests/test_api_answer_api.py
"""Tests for the answer API endpoints."""

import unittest
from unittest.mock import MagicMock, AsyncMock # Импортируем AsyncMock
from fastapi.testclient import TestClient
from api.answer_api import create_app
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker


class TestAnswerAPI(unittest.TestCase):
    """Test suite for the answer API endpoints."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock instances for dependencies
        self.mock_storage = MagicMock(spec=LocalStorage)
        self.mock_checker = MagicMock(spec=FIPIAnswerChecker) # Мок для всего класса
        self.app = create_app(self.mock_storage, self.mock_checker)
        self.client = TestClient(self.app)

    def test_get_initial_state(self):
        """Test the GET /initial_state/{page_name} endpoint."""
        # Arrange
        page_name = "test_page"
        expected_data = {
            f"{page_name}_task1": {"answer": "A", "status": "correct"},
            f"{page_name}_task2": {"answer": "B", "status": "incorrect"}
        }
        # Configure the mock to return specific data when _load_data is called
        self.mock_storage._load_data.return_value = expected_data.copy()

        # Act
        response = self.client.get(f"/initial_state/{page_name}")

        # Assert
        self.assertEqual(response.status_code, 200)
        # The API currently returns all data from _load_data
        # filtered by prefix internally, but the mock's _load_data is called.
        self.mock_storage._load_data.assert_called_once()
        # Note: The current API implementation returns *all* data from _load_data
        # filtered by prefix. The mock's returned data is used directly.
        # The response JSON should match the filtered data based on the mock's return value.
        # For this test, we'll assume the filtering logic in the API works correctly
        # and just check if the call to _load_data happened.
        # To test the filtering, we'd need a more complex mock setup.
        # For now, checking the call is sufficient given the mock's return value.
        self.assertEqual(response.json(), expected_data)

    def test_submit_answer_new(self):
        """Test the POST /submit_answer endpoint when the answer is new."""
        # Arrange
        task_id = "task_123"
        form_id = "form_123"
        user_answer = "My Answer"
        check_result = {
            "status": "correct",
            "message": "Correct",
            "raw_response": "..."
        }
        # Настройка мока storage: возвращает (None, "not_checked")
        self.mock_storage.get_answer_and_status.return_value = (None, "not_checked")

        # ИСПРАВЛЕНО: Используем AsyncMock для асинхронного метода check_answer
        # AsyncMock при вызове возвращает awaitable объект, который при await возвращает return_value
        mock_check_coroutine = AsyncMock(return_value=check_result)
        self.mock_checker.check_answer = mock_check_coroutine

        # Act
        response = self.client.post("/submit_answer", json={
            "task_id": task_id,
            "answer": user_answer,
            "form_id": form_id
        })

        # Assert
        # Теперь ожидаем статус 200, так как ошибка 500 была из-за неправильного мока
        self.assertEqual(response.status_code, 200)
        # Проверяем, что тело ответа соответствует результату проверки
        self.assertEqual(response.json(), check_result)
        # Проверяем, что метод get_answer_and_status был вызван с правильным task_id
        self.mock_storage.get_answer_and_status.assert_called_once_with(task_id)
        # Проверяем, что асинхронный метод check_answer был вызван с правильными аргументами
        mock_check_coroutine.assert_called_once_with(task_id, form_id, user_answer)
        # Проверяем, что метод save_answer_and_status был вызван с правильными аргументами
        self.mock_storage.save_answer_and_status.assert_called_once_with(task_id, user_answer, "correct")

    def test_submit_answer_cached(self):
        """Test the POST /submit_answer endpoint when the answer is already cached."""
        # Arrange
        task_id = "task_123"
        form_id = "form_123"
        cached_answer = "Cached Answer"
        cached_status = "correct"
        user_answer = "Different Answer" # Even if user submits a different one, cached is returned
        # Настройка мока storage: возвращает (cached_answer, cached_status)
        self.mock_storage.get_answer_and_status.return_value = (cached_answer, cached_status)

        # Act
        response = self.client.post("/submit_answer", json={
            "task_id": task_id,
            "answer": user_answer,
            "form_id": form_id
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        # Should return the cached status and the *cached* answer
        expected_response = {
             "status": cached_status,
             "message": f"Retrieved cached result: {cached_status}",
             "answer": cached_answer
        }
        self.assertEqual(response.json(), expected_response)
        self.mock_storage.get_answer_and_status.assert_called_once_with(task_id)
        # The checker should NOT have been called
        self.mock_checker.check_answer.assert_not_called()
        # The storage should NOT have been updated with the new answer
        self.mock_storage.save_answer_and_status.assert_not_called()

    def test_save_answer_only(self):
        """Test the POST /save_answer_only endpoint."""
        # Arrange
        task_id = "task_456"
        user_answer = "Saved Answer"

        # Act
        response = self.client.post("/save_answer_only", json={
            "task_id": task_id,
            "answer": user_answer
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn("saved successfully", response.json()["message"])
        self.mock_storage.save_answer_and_status.assert_called_once_with(task_id, user_answer, "not_checked")


if __name__ == "__main__":
    unittest.main()
