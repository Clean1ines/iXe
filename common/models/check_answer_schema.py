"""
Pydantic model representing a user's answer check request and response.
Used for the answer checking service API and internal processing.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CheckAnswerRequest(BaseModel):
    """
    Model representing a request to check a user's answer.

    Attributes:
        problem_id (str): Unique identifier of the problem to check against.
        user_answer (str): The answer provided by the user.
        subject (str): The subject of the problem (e.g., "math", "informatics").
        metadata (Optional[Dict[str, Any]]): Arbitrary additional data for the check. May be null.
    """
    problem_id: str
    user_answer: str
    subject: str = "math"
    metadata: Optional[Dict[str, Any]] = None


class CheckAnswerResponse(BaseModel):
    """
    Model representing the response from an answer check.

    Attributes:
        problem_id (str): Unique identifier of the checked problem.
        user_answer (str): The answer provided by the user.
        is_correct (bool): Whether the user's answer was correct.
        score (float): Numeric score achieved (0.0 to max_score).
        max_score (float): Maximum possible score for this problem.
        feedback (str): Text feedback on the answer.
        explanation (Optional[str]): Detailed explanation of correctness. May be null.
        checker_type (str): Type of checker used ("external_api", "rule_based", "llm", etc.).
        checked_at (datetime): ISO8601 timestamp when the check was performed.
        metadata (Optional[Dict[str, Any]]): Arbitrary additional data from the check. May be null.
        verdict: VerdictEnum  # Additional field for cognitive techniques
        score_float: float  # Additional field for cognitive techniques
        short_hint: str  # Additional field for cognitive techniques
        evidence: List[str] = Field(default_factory=list)  # Additional field for cognitive techniques
        deep_explanation_id: Optional[str] = None  # Additional field for cognitive techniques
        hint: Optional[str] = None  # Additional field for cognitive techniques
        next_task_suggestion: Optional[str] = None  # Additional field for cognitive techniques
    """
    problem_id: str
    user_answer: str
    is_correct: bool
    score: float
    max_score: float = 1.0
    feedback: str
    explanation: Optional[str] = None
    checker_type: str
    checked_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    # Additional fields for cognitive techniques (keeping backward compatibility)
    verdict: Optional[str] = None
    score_float: Optional[float] = None
    short_hint: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    deep_explanation_id: Optional[str] = None
    hint: Optional[str] = None
    next_task_suggestion: Optional[str] = None
