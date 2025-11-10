from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from domain.value_objects.problem_id import ProblemId

class ProgressStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class UserProgress:
    user_id: str
    problem_id: ProblemId
    status: ProgressStatus
    score: float = 0.0
    attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    started_at: datetime = datetime.now()

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if self.score < 0 or self.score > 1:
            raise ValueError("Score must be between 0 and 1")
        
        if self.attempts < 0:
            raise ValueError("Attempts cannot be negative")

    def record_attempt(self, is_correct: bool, score: float):
        """Обновляет прогресс на основе попытки."""
        self.attempts += 1
        self.last_attempt_at = datetime.now()
        self.score = max(self.score, score)
        
        if is_correct:
            self.status = ProgressStatus.COMPLETED
        else:
            self.status = ProgressStatus.IN_PROGRESS

    def can_retry(self) -> bool:
        """Проверяет, может ли пользователь повторить попытку."""
        # Пример бизнес-правила: не более 3 попыток в день
        if self.attempts >= 3 and self.last_attempt_at:
            time_since_last = datetime.now() - self.last_attempt_at
            return time_since_last.days >= 1
        return True
