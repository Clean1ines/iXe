"""Модуль для проверки ответов пользователя на задания FIPI через API."""

import logging # NEW: Import logging
import json
from typing import Dict, Any

import httpx


logger = logging.getLogger(__name__) # NEW: Create module logger

class FIPIAnswerChecker:
    """Класс для отправки пользовательских ответов на задания FIPI и получения результата проверки.

    Attributes:
        base_url (str): Базовый URL сайта FIPI (например, 'https://fipi.ru  ').
    """

    def __init__(self, base_url: str) -> None:
        """Инициализирует экземпляр FIPIAnswerChecker.

        Args:
            base_url (str): Базовый URL сайта FIPI.
        """
        self.base_url = base_url.rstrip("/")

    async def check_answer(self, task_id: str, form_id: str, user_answer: str) -> Dict[str, Any]:
        """Отправляет пользовательский ответ на задание FIPI и возвращает результат проверки.

        This method logs the attempt, request details, response, and outcome.

        Args:
            task_id (str): Идентификатор задания (например, '40B442').
            form_id (str): Идентификатор формы (например, 'checkform40B442').
            user_answer (str): Ответ, введённый пользователем.

        Returns:
            Dict[str, Any]: Словарь с ключами:
                - 'status': 'correct', 'incorrect' или 'error'
                - 'message': краткое текстовое описание результата
                - 'raw_response': исходный текст ответа от сервера (для отладки)
        """
        logger.info(f"Checking answer for task {task_id} using form {form_id}. Answer length: {len(user_answer)}") # NEW: Log start of check
        url = f"{self.base_url}/check-answer"  # Предполагаемый эндпоинт
        data = {
            "answer": user_answer,
            "task_id": task_id,
            "form_id": form_id,
        }
        headers = {
            "Referer": f"{self.base_url}/",
            "Origin": self.base_url,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (compatible; FIPIParser/1.0)",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.debug(f"Sending POST request to {url} with data keys: {list(data.keys())} and headers: {list(headers.keys())}") # MODIFIED: Log request details safely
                response = await client.post(url, data=data, headers=headers)
                response.raise_for_status()
                raw_text = response.text
                logger.debug(f"Received raw response: {raw_text[:200]}...") # NEW: Log raw response snippet

                # Пробуем распарсить JSON, как выяснили, сайт возвращает JSON
                try:
                    json_data = response.json()
                    logger.debug(f"Parsed JSON response: {json_data}") # NEW: Log parsed JSON
                    server_status = json_data.get("status")
                    server_message = json_data.get("message", raw_text)
                except (json.JSONDecodeError, AttributeError):
                    # Fallback: анализ текста, если JSON не удался
                    if "correct" in raw_text.lower() or "верно" in raw_text.lower():
                        server_status = "correct"
                        server_message = "Верно"
                    elif "incorrect" in raw_text.lower() or "неверно" in raw_text.lower():
                        server_status = "incorrect"
                        server_message = "Неверно"
                    else:
                        server_status = None
                        server_message = raw_text

                if server_status == "correct":
                    logger.info(f"Answer for task {task_id} is CORRECT.") # NEW: Log correct result
                    return {
                        "status": "correct",
                        "message": server_message,
                        "raw_response": raw_text,
                    }
                elif server_status == "incorrect":
                    logger.info(f"Answer for task {task_id} is INCORRECT.") # NEW: Log incorrect result
                    return {
                        "status": "incorrect",
                        "message": server_message,
                        "raw_response": raw_text,
                    }
                else:
                    logger.warning(f"Could not determine status for task {task_id}. Raw response: {raw_text[:100]}...") # NEW: Log undetermined status
                    return {
                        "status": "error",
                        "message": "Не удалось определить статус ответа.",
                        "raw_response": raw_text,
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} while checking answer for task {task_id}: {e}", exc_info=True) # MODIFIED: Use logger
            return {
                "status": "error",
                "message": f"HTTP ошибка: {e.response.status_code}",
                "raw_response": str(e),
            }
        except httpx.RequestError as e:
            logger.error(f"Request error while checking answer for task {task_id}: {type(e).__name__}, {e}", exc_info=True) # MODIFIED: Use logger
            return {
                "status": "error",
                "message": f"Сетевая ошибка: {type(e).__name__}",
                "raw_response": str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected error while checking answer for task {task_id}: {type(e).__name__}, {e}", exc_info=True) # MODIFIED: Use logger
            return {
                "status": "error",
                "message": f"Неизвестная ошибка: {type(e).__name__}",
                "raw_response": str(e),
            }

