# api/services/quiz_service_adapter.py
from typing import List
from fastapi import HTTPException
import uuid
import logging
from utils.database_manager import DatabaseManager
from api.schemas import StartQuizRequest, StartQuizResponse, QuizItem

logger = logging.getLogger(__name__)

class QuizServiceAdapter:
    """
    Adapter for QuizService to isolate web API from heavy dependencies like Qdrant.
    This adapter provides a simplified interface that the API can use without directly
    depending on QdrantProblemRetriever, InMemorySkillGraph, or SpecificationService.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initializes the adapter with only the database manager.

        Args:
            db: The database manager instance for data access.
        """
        self.db = db

    def start_quiz(self, request: StartQuizRequest) -> StartQuizResponse:
        """
        Initiates a new quiz based on the provided request.
        This is a simplified implementation that does not use Qdrant or adaptive logic,
        serving as a temporary solution until the full quiz service is externalized.

        Args:
            request: The request object containing quiz parameters.

        Returns:
            StartQuizResponse: The response object containing the quiz ID and items.
        """
        logger.info(f"Starting quiz via adapter for page: {request.page_name}, user: {request.user_id}, strategy: {request.strategy}")
        
        # For now, simply fetch problems from the database based on subject
        # This bypasses Qdrant and adaptive logic
        all_problems = self.db.get_all_problems()
        subject = request.page_name
        
        # Filter problems by subject
        filtered_problems = [
            p for p in all_problems
            if p.subject == subject or p.problem_id.startswith(f"{subject}_")
        ]
        
        # Limit to 10 problems for a basic quiz
        selected_problems = (filtered_problems or all_problems)[:10]

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

        quiz_id = f"quiz_{request.strategy}_{uuid.uuid4().hex[:8]}"
        return StartQuizResponse(quiz_id=quiz_id, items=items)
