from fastapi import APIRouter, Depends, HTTPException
from api.schemas import CheckAnswerRequest, CheckAnswerResponse
from api.services.answer_service import AnswerService
from api.dependencies import get_answer_service

router = APIRouter()

@router.post("/check_answer", response_model=CheckAnswerResponse)
async def check_answer_endpoint(
    request: CheckAnswerRequest,
    service: AnswerService = Depends(get_answer_service)
):
    return await service.check_answer(request)
