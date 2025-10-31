# api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Запросы ---
class StartQuizRequest(BaseModel):
    """
    Schema for requesting the start of a new quiz.

    Attributes:
        page_name: The subject or page identifier to start the quiz for.
    """
    page_name: str # <-- Сделаем обязательным для проверки валидации

class CheckAnswerRequest(BaseModel):
    """
    Schema for requesting answer validation.

    Attributes:
        problem_id: Unique identifier of the problem.
        user_answer: The answer provided by the user.
        form_id: Identifier of the form used for submission.
    """
    problem_id: str
    user_answer: str
    form_id: str

class GeneratePlanRequest(BaseModel):
    """
    Schema for requesting the generation of a study plan.
    Currently empty, can be extended with parameters like user goals, time, etc.
    """
    # Пока пустой, можно расширить параметрами генерации
    pass

# --- Ответы ---
class QuizItem(BaseModel):
    """
    Schema representing a single item within a quiz.

    Contains the problem details required for display and interaction.
    """
    problem_id: str
    subject: str
    topic: str
    prompt: str  # HTML
    choices_or_input_type: str

class StartQuizResponse(BaseModel):
    """
    Schema for the response to a quiz start request.

    Attributes:
        quiz_id: Unique identifier for the started quiz.
        items: List of quiz items to be presented to the user.
    """
    quiz_id: str
    items: List[QuizItem]

class CheckAnswerResponse(BaseModel):
    """
    Schema for the response to an answer check request.

    Attributes:
        verdict: The result of the check ('correct', 'incorrect', 'error').
        score_float: A numerical score (e.g., 1.0 for correct, 0.0 for incorrect).
        short_hint: A brief hint or message from the checker.
        evidence: A list of evidence items (currently empty).
        deep_explanation_id: Optional ID for a detailed explanation (currently null).
    """
    verdict: str  # "correct", "incorrect", "pending"
    score_float: float
    short_hint: str
    evidence: List[str]  # пока пустой список
    deep_explanation_id: Optional[str]
    # Убираем feedback, чтобы избежать потенциального конфликта
    # feedback: Optional[str] = None

class GeneratePlanResponse(BaseModel):
    """
    Schema for the response to a study plan generation request.

    Attributes:
        plan_id: Unique identifier for the generated plan.
        weeks: List of weeks/days in the plan (currently empty list).
    """
    plan_id: str
    weeks: List[dict]  # или более конкретная схема для недели

class AvailableSubjectsResponse(BaseModel):
    """
    Schema for the response listing available subjects.

    Attributes:
        subjects: List of subject names available in the system.
    """
    subjects: List[str]

# --- Модель задачи (для возврата из API, может быть подмножеством Problem из models) ---
class ProblemResponse(BaseModel):
    """
    Schema representing a problem for API responses.

    Attributes:
        problem_id: Unique identifier of the problem.
        subject: Subject the problem belongs to.
        text: The text of the problem.
        topics: List of topics covered by the problem.
        offline_html: Optional HTML content for offline use.
    """
    problem_id: str
    subject: str
    text: str
    topics: List[str]
    offline_html: Optional[str]
    # ... добавить другие нужные поля
    model_config = {"from_attributes": True} # <-- Используем новый способ
