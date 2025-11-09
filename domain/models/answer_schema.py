from pydantic import BaseModel
from typing import Optional, Dict, Any

class UserAnswer(BaseModel):
    """Represents a user's answer to a problem."""
    answer_text: str
    user_id: str
    problem_id: str
    timestamp: Optional[str] = None

class AnswerCheckResult(BaseModel):
    """Represents the result of checking a user's answer."""
    is_correct: bool
    score: float
    feedback: Dict[str, Any]
    solution: Optional[str] = None
    official_answer: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
