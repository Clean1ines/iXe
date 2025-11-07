"""Infrastructure adapter for task classification."""

from typing import List, Dict, Any
from domain.interfaces.html_processor import ITaskClassifier
from domain.interfaces.task_inferer import ITaskNumberInferer


class TaskClassifierAdapter(ITaskClassifier):
    """Infrastructure adapter implementing domain interface for task classification."""

    def __init__(self, task_inferer: ITaskNumberInferer):
        """
        Initialize the adapter.

        Args:
            task_inferer: Implementation of ITaskNumberInferer for inferring task numbers
        """
        self.task_inferer = task_inferer

    def classify_task(self, kes_codes: List[str], kos_codes: List[str], answer_type: str) -> Dict[str, Any]:
        """
        Classify a task based on KES/KOS codes and answer type.

        Args:
            kes_codes: List of KES codes
            kos_codes: List of KOS codes
            answer_type: Type of answer (short, extended, etc.)

        Returns:
            Dictionary with task number and related metadata
        """
        task_number = self.task_inferer.infer(kes_codes, answer_type) or 0
        difficulty_level = 'basic' if task_number <= 12 else 'advanced'
        max_score = 1 if task_number <= 12 else 2

        return {
            'task_number': task_number,
            'difficulty_level': difficulty_level,
            'max_score': max_score
        }
