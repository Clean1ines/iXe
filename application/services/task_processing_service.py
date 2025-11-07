from typing import List, Dict, Any, Optional
from domain.interfaces.task_inferer import ITaskNumberInferer
from domain.interfaces.html_processor import ITaskClassifier
from dataclasses import dataclass


@dataclass
class TaskClassificationResult:
    """Result of task classification."""
    task_number: Optional[int]
    difficulty_level: str
    max_score: int
    classification_confidence: float = 1.0


class TaskProcessingService:
    """Application service for task processing operations."""
    
    def __init__(
        self, 
        task_inferer: ITaskNumberInferer,
        task_classifier: ITaskClassifier
    ):
        self.task_inferer = task_inferer
        self.task_classifier = task_classifier

    def process_task_classification(
        self, 
        kes_codes: List[str], 
        kos_codes: List[str], 
        answer_type: str
    ) -> TaskClassificationResult:
        """
        Process task classification using domain interfaces.
        
        Args:
            kes_codes: List of KES codes
            kos_codes: List of KOS codes
            answer_type: Type of answer (short, extended, etc.)
            
        Returns:
            TaskClassificationResult with task number and related metadata
        """
        task_number = self.task_inferer.infer(kes_codes, answer_type) or 0
        classification_result = self.task_classifier.classify_task(kes_codes, kos_codes, answer_type)
        
        return TaskClassificationResult(
            task_number=task_number,
            difficulty_level=classification_result.get('difficulty_level', 'basic'),
            max_score=classification_result.get('max_score', 1)
        )
