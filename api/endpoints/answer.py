from fastapi import APIRouter, Request, Depends, HTTPException
import logging
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from api.dependencies import get_db_manager, get_storage, get_answer_checker

logger = logging.getLogger(__name__)
router = APIRouter()

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

        # Кэширование (только если не stateless)
        if storage is not None:
            cached_ans, cached_status = storage.get_answer_and_status(problem_id)
            if cached_ans is not None and cached_status in ("correct", "incorrect"):
                logger.info(f"Cache hit for {problem_id}")
                return {
                    "verdict": cached_status,
                    "score_float": 1.0 if cached_status == "correct" else 0.0,
                    "short_hint": "From cache",
                    "evidence": [],
                    "deep_explanation_id": None
                }

        # Проверка через FIPI
        result = await checker.check_answer(problem_id, form_id, user_answer)
        verdict = result["status"]
        message = result["message"]

        # Сохранение (только если не stateless)
        if storage is not None:
            storage.save_answer_and_status(problem_id, user_answer, verdict)

        return {
            "verdict": verdict,
            "score_float": 1.0 if verdict == "correct" else (0.0 if verdict == "incorrect" else -1.0),
            "short_hint": message,
            "evidence": [],
            "deep_explanation_id": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
