from fastapi import APIRouter, Request, Depends, HTTPException
import logging
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from api.dependencies import get_db_manager, get_storage, get_answer_checker
from services.specification import SpecificationService
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize specification service once at module level
# Adjust paths if specs are in a different location
SPEC_DIR = Path(__file__).parent.parent.parent / "data" / "specs"
SPEC_SERVICE = SpecificationService(
    spec_path=SPEC_DIR / "ege_2026_math_spec.json",
    kes_kos_path=SPEC_DIR / "ege_2026_math_kes_kos.json"
)

@router.post("/answer")
async def check_answer(
    request: Request,
    db: DatabaseManager = Depends(get_db_manager),
    storage: LocalStorage | None = Depends(get_storage),
    checker = Depends(get_answer_checker)
):
    try:
        data = await request.json()
        problem_id = data.get("problem_id")
        user_answer = data.get("user_answer")
        form_id = data.get("form_id")

        if not problem_id or user_answer is None or not form_id:
            raise HTTPException(status_code=422, detail="problem_id, user_answer, and form_id required")

        # Extract task_number from problem_id (e.g., "init_4CBD4E" → assume task_number from DB or fallback)
        # In real implementation, task_number should come from DBProblem
        # For now, we'll use a placeholder (e.g., always 18 for demo)
        # TODO: Fetch task_number from database via problem_id
        task_number = 18  # <-- REPLACE WITH DB LOOKUP IN PRODUCTION

        # Кэширование (только если не stateless)
        if storage is not None:
            cached_ans, cached_status = storage.get_answer_and_status(problem_id)
            if cached_ans is not None and cached_status in ("correct", "incorrect"):
                logger.info(f"Cache hit for {problem_id}")
                feedback = SPEC_SERVICE.get_feedback_for_task(task_number)
                return {
                    "verdict": cached_status,
                    "score_float": 1.0 if cached_status == "correct" else 0.0,
                    "short_hint": "Из кэша",
                    "feedback": feedback,
                    "evidence": [],
                    "deep_explanation_id": None
                }

        # Проверка через FIPI
        result = await checker.check_answer(problem_id, form_id, user_answer)
        verdict = result["status"]
        message = result["message"]

        # Генерация pedagogical feedback
        feedback = SPEC_SERVICE.get_feedback_for_task(task_number)

        # Сохранение (только если не stateless)
        if storage is not None:
            storage.save_answer_and_status(problem_id, user_answer, verdict)

        return {
            "verdict": verdict,
            "score_float": 1.0 if verdict == "correct" else (0.0 if verdict == "incorrect" else -1.0),
            "short_hint": message,
            "feedback": feedback,
            "evidence": [],
            "deep_explanation_id": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
