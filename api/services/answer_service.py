from fastapi import HTTPException
import logging
from typing import Optional
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from api.schemas import CheckAnswerRequest, CheckAnswerResponse, Feedback
from common.services.specification import SpecificationService
from utils.skill_graph import InMemorySkillGraph
from common.utils.task_id_utils import extract_task_id_and_form_id

logger = logging.getLogger(__name__)


class AnswerService:
    """
    Service class for handling answer validation and caching logic.
    """

    def __init__(
        self,
        db: DatabaseManager,
        checker: FIPIAnswerChecker, # Renamed from 'answer_checker' to 'checker' to match dependencies.py, but type is FIPIAnswerChecker
        storage: Optional[LocalStorage],
        skill_graph: InMemorySkillGraph,
        spec_service: SpecificationService
    ):
        self.db = db
        self.checker = checker # This is now an instance of FIPIAnswerChecker
        self.storage = storage
        self.skill_graph = skill_graph
        self.spec_service = spec_service

    async def check_answer(self, request: CheckAnswerRequest) -> CheckAnswerResponse:
        problem_id = request.problem_id
        user_answer = request.user_answer
        # form_id is not used directly here anymore as FIPIAnswerChecker gets subject

        # Получаем задачу из БД для извлечения task_number и subject
        db_problem = self.db.get_problem_by_id(problem_id)
        if not db_problem:
            raise HTTPException(status_code=404, detail="Problem not found in database")
        task_number = db_problem.task_number
        problem_subject = db_problem.subject # Assuming DBProblem has a 'subject' field

        # 1. Проверка кэша
        cached_response = await self._check_cache(problem_id, task_number)
        if cached_response:
            return cached_response

        # 2. Проверка через внешний API (теперь через FIPIAnswerChecker с BrowserManager)
        verdict, message = await self._call_external_checker(problem_id, user_answer, problem_subject)

        # 3. Сохранение результата
        await self._save_result(problem_id, user_answer, verdict)

        # 4. Формирование ответа
        return await self._generate_feedback(task_number, verdict, message, user_answer)

    async def _check_cache(self, problem_id: str, task_number: int) -> Optional[CheckAnswerResponse]:
        """Checks the local cache for a result."""
        if self.storage is not None:
            cached_ans, cached_status = self.storage.get_answer_and_status(problem_id)
            if cached_ans is not None and cached_status in ("correct", "incorrect"):
                logger.info(f"Cache hit for {problem_id}")
                feedback = self.spec_service.get_feedback_for_task(task_number)
                return CheckAnswerResponse(
                    verdict=cached_status,
                    score_float=1.0 if cached_status == "correct" else 0.0,
                    short_hint="From cache",
                    evidence=[],
                    deep_explanation_id=None,
                    feedback=feedback
                )
        return None

    async def _call_external_checker(self, problem_id: str, user_answer: str, problem_subject: str) -> tuple[str, str]:
        """Calls the external answer checker (FIPIAnswerChecker)."""
        try:
            # Extract task_id and form_id from the problem_id using the utility function
            task_id, form_id = extract_task_id_and_form_id(problem_id)
            # Call the updated FIPIAnswerChecker.check_answer with subject
            result = await self.checker.check_answer(task_id, form_id, user_answer, problem_subject)
            return result["status"], result["message"]
        except Exception as e:
            logger.error(f"Error calling answer checker for {problem_id}: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail="Error checking answer with external service")

    async def _save_result(self, problem_id: str, user_answer: str, verdict: str) -> None:
        """Saves the check result to local storage."""
        if self.storage is not None:
            self.storage.save_answer_and_status(problem_id, user_answer, verdict)

    async def _generate_feedback(self, task_number: int, verdict: str, message: str, user_answer: str) -> CheckAnswerResponse:
        """Generates a response with feedback and adaptive recommendations."""
        score = 1.0 if verdict == "correct" else (0.0 if verdict == "incorrect" else -1.0)
        feedback = self.spec_service.get_feedback_for_task(task_number)

        # --- Adaptive Recommendations ---
        next_steps = []
        if self.skill_graph and verdict == "incorrect":
            missing_skills = self.skill_graph.get_codes_for_task(task_number)
            if missing_skills:
                # Limit the number of skills in the recommendation
                relevant_skills = missing_skills[:2]
                skill_descriptions_list = [
                    self.skill_graph.skill_descriptions.get(code, f"Skill {code}")
                    for code in relevant_skills
                ]
                next_steps.append(f"Review: {', '.join(skill_descriptions_list)}")

                task_spec = self.spec_service.get_task_spec(task_number)
                if task_spec:
                    task_desc = task_spec.get("description", "this topic")
                    next_steps.append(f"Solve 2 problems on '{task_desc[:40]}...'")  # Truncate for brevity
                else:
                    next_steps.append(f"Solve 2 problems on task {task_number} topic")

        # Update feedback with next_steps if they exist
        if next_steps:
            updated_feedback = feedback.model_copy()
            updated_feedback = feedback.model_copy(update={"next_steps": next_steps})
        else:
            updated_feedback = feedback

        return CheckAnswerResponse(
            verdict=verdict,
            score_float=score,
            short_hint=message,
            evidence=[],
            deep_explanation_id=None,
            feedback=updated_feedback
        )

