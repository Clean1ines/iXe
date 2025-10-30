# api/endpoints/answer.py
from fastapi import APIRouter, Depends, HTTPException
from api.schemas import CheckAnswerRequest, CheckAnswerResponse
from api.services.answer_service import AnswerService
from api.dependencies import get_answer_service

router = APIRouter()

@router.post("/answer", response_model=CheckAnswerResponse)
async def check_answer(
    request: CheckAnswerRequest, # Pydantic-валидация входных данных!
    service: AnswerService = Depends(get_answer_service)
):
    # Эндпоинт теперь тонкая обёртка
    try:
        return await service.check_answer(request)
    except HTTPException:
        # Пробрасываем HTTPException дальше, чтобы FastAPI корректно обработал
        raise
    except Exception:
        # Пробрасываем, чтобы централизованная обработка сработала
        raise
