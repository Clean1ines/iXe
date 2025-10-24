"""Тесты для модуля answer_checker."""

import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from httpx import Response

from utils.answer_checker import FIPIAnswerChecker


class TestFIPIAnswerChecker(unittest.IsolatedAsyncioTestCase):
    """Тесты для класса FIPIAnswerChecker."""

    def setUp(self) -> None:
        self.checker = FIPIAnswerChecker("https://fipi.ru")

    async def test_check_answer_correct(self) -> None:
        """Тест успешной проверки правильного ответа."""
        # Мокаем JSON-ответ сервера
        mock_json_response = {"status": "correct", "message": "Верно"}
        mock_response = Response(
            status_code=200,
            text=json.dumps(mock_json_response),
            request=httpx.Request("POST", "https://fipi.ru/check-answer"),
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await self.checker.check_answer(
                task_id="40B442",
                form_id="checkform40B442",
                user_answer="42"
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            posted_data = call_args.kwargs.get("data", {})

            self.assertEqual(posted_data.get("answer"), "42")
            self.assertEqual(posted_data.get("task_id"), "40B442")
            self.assertEqual(posted_data.get("form_id"), "checkform40B442")

            self.assertEqual(result["status"], "correct")
            self.assertEqual(result["message"], "Верно")

    async def test_check_answer_error(self) -> None:
        """Тест обработки HTTP 500 ошибки."""
        mock_response = Response(
            status_code=500,
            text="Internal Server Error",
            request=httpx.Request("POST", "https://fipi.ru/check-answer"),
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await self.checker.check_answer(
                task_id="40B442",
                form_id="checkform40B442",
                user_answer="42"
            )

            self.assertEqual(result["status"], "error")
            self.assertIn("HTTP ошибка: 500", result["message"])