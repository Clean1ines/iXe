# api/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Запросы ---
class StartQuizRequest(BaseModel):
    page_name: str = "init"

class CheckAnswerRequest(BaseModel):
    problem_id: str
    user_answer: str
    form_id: str

class GeneratePlanRequest(BaseModel):
    # Пока пустой, можно расширить параметрами генерации
    pass

# --- Ответы ---
class QuizItem(BaseModel):
    problem_id: str
    subject: str
    topic: str
    prompt: str  # HTML
    choices_or_input_type: str

class StartQuizResponse(BaseModel):
    quiz_id: str
    items: List[QuizItem]

class CheckAnswerResponse(BaseModel):
    verdict: str  # "correct", "incorrect", "pending"
    score_float: float
    short_hint: str
    evidence: List[str]  # пока пустой список
    deep_explanation_id: Optional[str]

class GeneratePlanResponse(BaseModel):
    plan_id: str
    weeks: List[dict]  # или более конкретная схема для недели

class AvailableSubjectsResponse(BaseModel):
    subjects: List[str]

# --- Модель задачи (для возврата из API, может быть подмножеством Problem из models) ---
# Убраны классы ProblemResponse и ProblemResponseV2, которые использовали deprecated config
class ProblemResponse(BaseModel):
    problem_id: str
    subject: str
    text: str
    topics: List[str]
    offline_html: Optional[str]
    # ... добавить другие нужные поля
    model_config = {"from_attributes": True} # <-- Используем новый способ
