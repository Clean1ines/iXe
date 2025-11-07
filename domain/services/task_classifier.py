"""Domain service for classifying tasks based on KES/KOS codes."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from utils.task_number_inferer import TaskNumberInferer
from services.specification import SpecificationService


@dataclass
class TaskClassificationResult:
    """Result of task classification."""
    task_number: Optional[int]
    difficulty_level: str
    max_score: int
    classification_confidence: float = 1.0


class TaskClassificationService:
    """Service for classifying tasks based on KES/KOS codes and other metadata."""

    def __init__(self, task_inferer: TaskNumberInferer):
        """
        Initialize the service.

        Args:
            task_inferer: TaskNumberInferer instance for inferring task numbers
        """
        self.task_inferer = task_inferer

    def classify_task(self, kes_codes: List[str], kos_codes: List[str], answer_type: str) -> TaskClassificationResult:
        """
        Classify a task based on KES/KOS codes and answer type.

        Args:
            kes_codes: List of KES codes
            kos_codes: List of KOS codes
            answer_type: Type of answer (short, extended, etc.)

        Returns:
            TaskClassificationResult with task number and related metadata
        """
        task_number = self.task_inferer.infer(kes_codes, answer_type) or 0
        difficulty_level = 'basic' if task_number <= 12 else 'advanced'
        max_score = 1 if task_number <= 12 else 2

        return TaskClassificationResult(
            task_number=task_number,
            difficulty_level=difficulty_level,
            max_score=max_score
        )
