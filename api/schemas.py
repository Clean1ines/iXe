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
    page_name: str

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
    pass

# --- Feedback model ---
class Feedback(BaseModel):
    """
    Pedagogical feedback based on FIPI specifications.
    """
    kos_explanation: str
    kes_topics: List[str]
    next_steps: List[str]

# --- Ответы ---
class QuizItem(BaseModel):
    """
    Schema representing a single item within a quiz.
    """
    problem_id: str
    subject: str
    topic: str
    prompt: str  # HTML
    choices_or_input_type: str

class StartQuizResponse(BaseModel):
    """
    Schema for the response to a quiz start request.
    """
    quiz_id: str
    items: List[QuizItem]

class CheckAnswerResponse(BaseModel):
    """
    Schema for the response to an answer check request.
    """
    verdict: str  # "correct", "incorrect", "error"
    score_float: float
    short_hint: str
    evidence: List[str]
    deep_explanation_id: Optional[str]
    feedback: Optional[Feedback] = None  # <-- Добавлено

class GeneratePlanResponse(BaseModel):
    """
    Schema for the response to a study plan generation request.
    """
    plan_id: str
    weeks: List[dict]

class AvailableSubjectsResponse(BaseModel):
    """
    Schema for the response listing available subjects.
    """
    subjects: List[str]

class ProblemResponse(BaseModel):
    """
    Schema representing a problem for API responses.
    """
    problem_id: str
    subject: str
    text: str
    topics: List[str]
    offline_html: Optional[str]
    model_config = {"from_attributes": True}
