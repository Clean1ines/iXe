# api/endpoints/quiz.py
from fastapi import APIRouter, Depends, HTTPException
from api.schemas import StartQuizRequest, StartQuizResponse
from api.services.quiz_service import QuizService
from api.dependencies import get_quiz_service

router = APIRouter()

@router.post("/quiz/daily/start", response_model=StartQuizResponse)
async def start_daily_quiz(
    request: StartQuizRequest,
    service: QuizService = Depends(get_quiz_service)
):
    # Эндпоинт теперь тонкая обёртка
    try:
        return service.start_quiz(request)
    except Exception:
        # Можно оставить обработку здесь, если нужна специфичная логика,
        # иначе пусть обрабатывается глобально
        raise # Пробрасываем, чтобы централизованная обработка сработала
