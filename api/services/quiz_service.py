# api/services/quiz_service.py
from typing import List
from fastapi import HTTPException
import uuid
import logging
from utils.database_manager import DatabaseManager
from api.schemas import StartQuizRequest, StartQuizResponse, QuizItem

logger = logging.getLogger(__name__)

class QuizService:
    """
    Service class for handling quiz-related business logic.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initializes the QuizService with a database manager.

        Args:
            db: The database manager instance for data access.
        """
        self.db = db

    def start_quiz(self, request: StartQuizRequest) -> StartQuizResponse:
        """
        Initiates a new quiz based on the provided request.

        Args:
            request: The request object containing quiz parameters (e.g., page_name).

        Returns:
            StartQuizResponse: The response object containing the quiz ID and items.

        Raises:
            HTTPException: If an error occurs during quiz creation.
        """
        logger.info(f"Starting quiz for page: {request.page_name}")
        # Убираем try/except, позволяя исключениям всплывать
        # try:
        all_problems = self.db.get_all_problems()
        # Фильтрация: пример, можно усложнить
        filtered = [
            p for p in all_problems
            if p.subject == request.page_name or p.problem_id.startswith(f"{request.page_name}_")
        ]
        selected_problems = (filtered or all_problems)[:10] # Берём первые 10

        items = []
        for p in selected_problems:
            prompt = p.offline_html or p.text
            items.append(QuizItem(
                problem_id=p.problem_id,
                subject=p.subject,
                topic=p.topics[0] if p.topics else "general",
                prompt=prompt,
                choices_or_input_type="text_input" # или определить из p.type
            ))

        quiz_id = f"daily_quiz_{uuid.uuid4().hex[:8]}"
        return StartQuizResponse(quiz_id=quiz_id, items=items)
        # except Exception as e: # <-- Убираем блок except
        #     logger.error(f"Quiz start error: {e}", exc_info=True)
        #     # Сервис может бросать HTTPException или возвращать Result-объект
        #     # Здесь мы пробрасываем, чтобы обработать в эндпоинте или глобально
        #     raise # <-- Это было: raise
        # Теперь исключение, если оно произойдёт, всплывёт в эндпоинт

