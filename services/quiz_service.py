from typing import List
from fastapi import HTTPException
import uuid
import logging
from utils.database_manager import DatabaseManager
from api.schemas import StartQuizRequest, StartQuizResponse, QuizItem
from services.base_service import BaseService
from utils.retriever import QdrantProblemRetriever
from utils.skill_graph import InMemorySkillGraph
from services.specification import SpecificationService


class QuizService(BaseService):
    """
    Service class for handling quiz-related business logic.
    """

    def __init__(self, db: DatabaseManager, retriever: QdrantProblemRetriever, skill_graph: InMemorySkillGraph, spec_service: SpecificationService):
        """
        Initializes the QuizService with a database manager and adaptive components.

        Args:
            db: The database manager instance for data access.
            retriever: Component for retrieving problems based on embeddings.
            skill_graph: Component for tracking and modeling user skills.
            spec_service: Component for applying exam specifications.
        """
        super().__init__(db)
        self.retriever = retriever
        self.skill_graph = skill_graph
        self.spec_service = spec_service

    async def initialize(self):
        """Initialize service-specific resources."""
        self.logger.info("QuizService initialized")

    def start_quiz(self, request: StartQuizRequest) -> StartQuizResponse:
        """
        Initiates a new quiz based on the provided request and user's progress.

        Args:
            request: The request object containing quiz parameters (e.g., page_name, user_id, strategy).

        Returns:
            StartQuizResponse: The response object containing the quiz ID and items.

        Raises:
            HTTPException: If an error occurs during quiz creation.
        """
        self.logger.info(f"Starting quiz for page: {request.page_name}, user: {request.user_id}, strategy: {request.strategy}")
        all_problems = self.db.get_all_problems()

        # Determine strategy and fetch problems accordingly
        selected_problems = self._select_problems_by_strategy(request, all_problems)

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

    def _select_problems_by_strategy(self, request: StartQuizRequest, all_problems: List['Problem']) -> List['Problem']:
        """
        Selects problems based on the specified strategy and user's skill graph.
        """
        strategy = request.strategy
        user_id = request.user_id
        subject = request.page_name

        if strategy == "calibration":
            # For calibration, select a diverse set of problems covering main topics
            return self._get_calibration_problems(subject, all_problems)
        elif strategy == "adaptive":
            # For adaptive, select problems based on user's skill graph and difficulty
            return self._get_adaptive_problems(user_id, subject, all_problems)
        elif strategy == "final":
            # For final, select problems based on exam specifications and user's weak areas
            return self._get_final_problems(user_id, subject, all_problems)
        else:
            # Default fallback to simple filtering, capped at 10
            filtered = [
                p for p in all_problems
                if p.subject == subject or p.problem_id.startswith(f"{subject}_")
            ]
            return (filtered or all_problems)[:10]

    def _get_calibration_problems(self, subject: str, all_problems: List['Problem']) -> List['Problem']:
        """
        Retrieves a set of problems for initial skill calibration.
        """
        # Example: Get 10 problems of varying difficulty from the subject
        filtered_by_subject = [p for p in all_problems if p.subject == subject]
        # Sort or sample based on task_number or other criteria for diversity
        sorted_problems = sorted(filtered_by_subject, key=lambda x: x.task_number)
        # Pick every Nth problem to ensure coverage across the exam structure
        step = max(1, len(sorted_problems) // 10)
        selected = sorted_problems[::step][:10]
        return selected

    def _get_adaptive_problems(self, user_id: str, subject: str, all_problems: List['Problem']) -> List['Problem']:
        """
        Retrieves problems based on the user's skill graph and adaptive logic.
        """
        # Get user's current skill state from the graph
        user_skills = self.skill_graph.get_user_skills(user_id, subject)
        # Example: Identify weak topics or skills
        weak_topics = self.skill_graph.get_weak_areas(user_id, subject)
        # Use the retriever to find relevant problems based on weak areas or next learning steps
        filtered_by_subject = [p for p in all_problems if p.subject == subject]
        # Placeholder: select based on weak topics or next difficulty level
        return filtered_by_subject[:10]

    def _get_final_problems(self, user_id: str, subject: str, all_problems: List['Problem']) -> List['Problem']:
        """
        Retrieves problems for a final exam simulation based on specifications.
        """
        # Get exam structure and user's historical performance
        exam_spec = self.spec_service.get_exam_specification(subject)
        user_history = self.skill_graph.get_user_history(user_id, subject)
        # Identify areas for targeted practice based on spec and history
        filtered_by_subject = [p for p in all_problems if p.subject == subject]
        # Placeholder: select based on exam spec requirements
        return filtered_by_subject[:10]
