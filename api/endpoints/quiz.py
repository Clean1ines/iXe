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
) -> StartQuizResponse:
    """
    API endpoint to start a new daily quiz.

    This endpoint takes a subject/page name and returns a list of quiz items
    along with a unique quiz ID.
    """
    # Убираем try/except, позволяя исключениям всплывать
    # try:
    return service.start_quiz(request)
    # except HTTPException:
    #     raise
    # except Exception:
    #     # Пробрасываем, чтобы централизованная обработка сработала
    #     raise
    # Теперь исключение, если оно произойдёт, всплывёт к глобальному обработчику

