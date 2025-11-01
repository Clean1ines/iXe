from fastapi import HTTPException
import logging
from typing import Optional
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from api.schemas import CheckAnswerRequest, CheckAnswerResponse, Feedback
from services.specification import SpecificationService
from utils.skill_graph import InMemorySkillGraph

logger = logging.getLogger(__name__)


class AnswerService:
    """
    Service class for handling answer validation and caching logic.
    """

    def __init__(
        self,
        db: DatabaseManager,
        checker: FIPIAnswerChecker,
        storage: Optional[LocalStorage],
        skill_graph: InMemorySkillGraph,
        spec_service: SpecificationService
    ):
        self.db = db
        self.checker = checker
        self.storage = storage
        self.skill_graph = skill_graph
        self.spec_service = spec_service

    async def check_answer(self, request: CheckAnswerRequest) -> CheckAnswerResponse:
        problem_id = request.problem_id
        user_answer = request.user_answer
        form_id = request.form_id

        # Получаем задачу из БД для извлечения task_number
        db_problem = self.db.get_problem_by_id(problem_id)
        if not db_problem:
            raise HTTPException(status_code=404, detail="Problem not found in database")
        task_number = db_problem.task_number

        # 1. Проверка кэша
        cached_response = await self._check_cache(problem_id, task_number)
        if cached_response:
            return cached_response

        # 2. Проверка через внешний API
        verdict, message = await self._call_external_checker(problem_id, form_id, user_answer)

        # 3. Сохранение результата
        await self._save_result(problem_id, user_answer, verdict)

        # 4. Формирование ответа
        return await self._generate_feedback(task_number, verdict, message, user_answer)

    async def _check_cache(self, problem_id: str, task_number: int) -> Optional[CheckAnswerResponse]:
        """Проверяет наличие результата в локальном кэше."""
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

    async def _call_external_checker(self, problem_id: str, form_id: str, user_answer: str) -> tuple[str, str]:
        """Вызывает внешний сервис проверки ответа."""
        try:
            result = await self.checker.check_answer(problem_id, form_id, user_answer)
            return result["status"], result["message"]
        except Exception as e:
            logger.error(f"Error calling answer checker for {problem_id}: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail="Error checking answer with external service")

    async def _save_result(self, problem_id: str, user_answer: str, verdict: str) -> None:
        """Сохраняет результат проверки в локальное хранилище."""
        if self.storage is not None:
            self.storage.save_answer_and_status(problem_id, user_answer, verdict)

    async def _generate_feedback(self, task_number: int, verdict: str, message: str, user_answer: str) -> CheckAnswerResponse:
        """Формирует ответ с обратной связью и адаптивными рекомендациями."""
        score = 1.0 if verdict == "correct" else (0.0 if verdict == "incorrect" else -1.0)
        feedback = self.spec_service.get_feedback_for_task(task_number)

        # --- Адаптивные рекомендации ---
        next_steps = []
        if self.skill_graph and verdict == "incorrect":
            missing_skills = self.skill_graph.get_prerequisites_for_task(task_number)
            if missing_skills:
                # Ограничиваем количество навыков в рекомендации
                relevant_skills = missing_skills[:2]
                skill_descriptions_list = [
                    self.skill_graph.skill_descriptions.get(code, f"Навык {code}")
                    for code in relevant_skills
                ]
                next_steps.append(f"Повторите: {', '.join(skill_descriptions_list)}")

                task_spec = self.spec_service.get_task_spec(task_number)
                if task_spec:
                    task_desc = task_spec.get("description", "данной теме")
                    next_steps.append(f"Решите 2 задачи по теме '{task_desc[:40]}...'")  # Обрезаем для краткости
                else:
                    next_steps.append(f"Решите 2 задачи по теме задания {task_number}")

        # Обновляем feedback с next_steps, если они есть
        if next_steps:
            updated_feedback = feedback.copy()
            updated_feedback["next_steps"] = next_steps
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
