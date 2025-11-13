"""
Domain model representing an EGE problem with business logic and invariants.

This is the core domain entity that encapsulates business rules and validation
for EGE problems, following Domain-Driven Design principles with rich behavior
instead of anemic data models.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

from domain.value_objects.problem_id import ProblemId
from domain.value_objects.problem_type import ProblemType
from domain.value_objects.difficulty_level import DifficultyLevel
from domain.value_objects.problem_status import ProblemStatus


@dataclass
class Problem:
    """
    Domain model representing an EGE problem with business logic.

    This class contains business rules and validation logic for EGE problems,
    following Domain-Driven Design principles. Unlike the anemic Pydantic model,
    this class includes behavior and invariants that maintain business consistency.

    Attributes:
        problem_id (ProblemId): Unique problem identifier value object.
        subject (str): Subject name, e.g., "mathematics", "informatics", "russian".
        problem_type (ProblemType): Problem type according to EGE format value object.
        text (str): Full problem statement, including LaTeX markup.
        difficulty_level (DifficultyLevel): Official EGE difficulty level value object.
        exam_part (str): Exam section: "Part 1" or "Part 2".
        max_score (int): Maximum score achievable for this problem (typically 1-4).
        status (ProblemStatus): Current status of the problem (draft, published, archived).
        answer (Optional[str]): Canonical answer string; may be null for open-ended or unsolved problems.
        options (Optional[List[str]]): Multiple-choice options if applicable. May be null.
        solutions (Optional[List[Dict[str, Any]]]): List of solution dictionaries, each containing fields like
            'solution_id', 'text', 'author'. May be null.
        kes_codes (List[str]): List of KES codes (Content Elements Classifier) identifying curriculum topics,
            e.g., ["1.2.3", "2.1"].
        skills (Optional[List[str]]): List of skill identifiers. May be null.
        task_number (Optional[int]): Position of the problem in the exam paper (1–19). May be null.
        kos_codes (List[str]): List of KOS codes (Requirements Classifier) specifying expected competencies.
        form_id (Optional[str]): Identifier of the answer submission form extracted from FIPI page. May be null.
        source_url (Optional[str]): Original FIPI URL of the problem. May be null.
        raw_html_path (Optional[str]): Path to saved raw HTML file, if preserved. May be null.
        created_at (datetime): ISO8601 timestamp when the record was created.
        updated_at (Optional[datetime]): ISO8601 timestamp of last update. May be null.
        metadata (Optional[Dict[str, Any]]): Arbitrary additional data. May be null.
        topics (List[str]): Curriculum topics covered by the problem (mapped from kes_codes for DB compatibility).
    """
    problem_id: ProblemId
    subject: str
    problem_type: ProblemType
    text: str
    difficulty_level: DifficultyLevel
    exam_part: str  # Must be "Part 1" or "Part 2"
    max_score: int = 1
    status: ProblemStatus = None  # Will be set in post_init
    answer: Optional[str] = None
    options: Optional[List[str]] = None
    solutions: Optional[List[Dict[str, Any]]] = None
    kes_codes: List[str] = None
    skills: Optional[List[str]] = None
    task_number: Optional[int] = None
    kos_codes: List[str] = None
    form_id: Optional[str] = None
    source_url: Optional[str] = None
    raw_html_path: Optional[str] = None
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    topics: List[str] = None  # Added for DB compatibility with topics field

    def __post_init__(self):
        """Validate the problem after initialization and set default values."""
        if self.kes_codes is None:
            self.kes_codes = []
        if self.kos_codes is None:
            self.kos_codes = []
        if self.topics is None:
            # Use kes_codes as topics for DB compatibility
            self.topics = self.kes_codes[:]
        if self.status is None:
            # Set default status
            from domain.value_objects.problem_status import ProblemStatus, ProblemStatusEnum
            self.status = ProblemStatus(ProblemStatusEnum.DRAFT)
        if self.created_at is None:
            self.created_at = datetime.now()
        
        if self.updated_at is None:
            self.updated_at = datetime.now()
        
        self._validate()

    def _validate(self):
        """Validate business rules and invariants for the problem."""
        if not self.subject or not self.subject.strip():
            raise ValueError("Subject cannot be empty")
        
        if self.max_score <= 0:
            raise ValueError("Max score must be positive")
        
        if self.task_number is not None and (self.task_number < 1 or self.task_number > 19):
            raise ValueError("Task number must be between 1 and 19")
        
        if self.exam_part not in ["Part 1", "Part 2"]:
            raise ValueError("Exam part must be either 'Part 1' or 'Part 2'")

    def is_answer_type_valid(self, answer: str) -> bool:
        """
        Check if the answer type matches the expected type for this problem.

        Args:
            answer: The answer string to validate.

        Returns:
            True if the answer type is valid, False otherwise.
        """
        if self.problem_type.value.name == "NUMBER":
            try:
                float(answer)
                return True
            except ValueError:
                return False
        elif self.problem_type.value.name == "TEXT":
            return isinstance(answer, str) and len(answer.strip()) > 0
        elif self.problem_type.value.name == "MULTIPLE_CHOICE":
            return answer in (self.options or [])
        return True

    def calculate_score(self, user_answer: str) -> int:
        """
        Calculate the score for a user's answer based on the problem's answer key.

        This is a simplified scoring mechanism. In a real system, this would likely
        delegate to an external service for complex answer checking.

        Args:
            user_answer: The user's answer string.

        Returns:
            The score (0 to max_score) for the given answer.
        """
        if not self.is_answer_type_valid(user_answer):
            return 0
        
        # Simple string comparison - in real system would use external checker
        if self.answer and user_answer.strip().lower() == self.answer.strip().lower():
            return self.max_score
        return 0

    def can_retry(self) -> bool:
        """
        Check if the problem can be attempted again.

        Returns:
            True if the problem can be retried, False otherwise.
        """
        # By default, problems can be retried unless business rules say otherwise
        return True

    def get_required_skills(self) -> List[str]:
        """
        Get the list of required skills for solving this problem.

        Returns:
            List of skill identifiers required for this problem.
        """
        return self.skills or []

    def is_published(self) -> bool:
        """
        Check if the problem is in published status.

        Returns:
            True if the problem is published, False otherwise.
        """
        from domain.value_objects.problem_status import ProblemStatusEnum
        return self.status.value == ProblemStatusEnum.PUBLISHED

    def mark_archived(self):
        """
        Mark the problem as archived, preventing further use in quizzes.
        """
        from domain.value_objects.problem_status import ProblemStatusEnum
        self.status = ProblemStatus(ProblemStatusEnum.ARCHIVED)
        self.updated_at = datetime.now()
