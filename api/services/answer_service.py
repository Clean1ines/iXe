# api/services/answer_service.py
from fastapi import HTTPException
import logging
from typing import Optional
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from api.schemas import CheckAnswerRequest, CheckAnswerResponse, Feedback
from services.specification import SpecificationService
from pathlib import Path

logger = logging.getLogger(__name__)

# Инициализация SpecificationService
SPEC_DIR = Path(__file__).parent.parent.parent / "data" / "specs"
SPEC_SERVICE = SpecificationService(
    spec_path=SPEC_DIR / "ege_2026_math_spec.json",
    kes_kos_path=SPEC_DIR / "ege_2026_math_kes_kos.json"
)

class AnswerService:
    """
    Service class for handling answer validation and caching logic.
    """

    def __init__(self, db: DatabaseManager, checker: FIPIAnswerChecker, storage: Optional[LocalStorage] = None):
        self.db = db
        self.checker = checker
        self.storage = storage

    async def check_answer(self, request: CheckAnswerRequest) -> CheckAnswerResponse:
        problem_id = request.problem_id
        user_answer = request.user_answer
        form_id = request.form_id

        # Получаем задачу из БД для извлечения task_number
        db_problem = self.db.get_problem_by_id(problem_id)
        if not db_problem:
            raise HTTPException(status_code=404, detail="Problem not found in database")
        task_number = db_problem.task_number

        # Генерация pedagogical feedback
        feedback = SPEC_SERVICE.get_feedback_for_task(task_number)

        # 1. Проверка кэша
        if self.storage is not None:
            cached_ans, cached_status = self.storage.get_answer_and_status(problem_id)
            if cached_ans is not None and cached_status in ("correct", "incorrect"):
                logger.info(f"Cache hit for {problem_id}")
                return CheckAnswerResponse(
                    verdict=cached_status,
                    score_float=1.0 if cached_status == "correct" else 0.0,
                    short_hint="From cache",
                    evidence=[],
                    deep_explanation_id=None,
                    feedback=feedback
                )

        # 2. Проверка через внешний API
        try:
            result = await self.checker.check_answer(problem_id, form_id, user_answer)
            verdict = result["status"]
            message = result["message"]
        except Exception as e:
            logger.error(f"Error calling answer checker for {problem_id}: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail="Error checking answer with external service")

        # 3. Сохранение результата
        if self.storage is not None:
            self.storage.save_answer_and_status(problem_id, user_answer, verdict)

        # 4. Формирование ответа
        score = 1.0 if verdict == "correct" else (0.0 if verdict == "incorrect" else -1.0)
        return CheckAnswerResponse(
            verdict=verdict,
            score_float=score,
            short_hint=message,
            evidence=[],
            deep_explanation_id=None,
            feedback=feedback
        )
