"""
Pydantic model representing an EGE problem scraped from the FIPI website.
Contains all necessary attributes of a problem in a unified format.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Problem(BaseModel):
    """
    Model representing an EGE problem.

    Attributes:
        problem_id (str): Unique problem identifier, e.g., 'init_0_40B442'.
        subject (str): Subject name, e.g., "mathematics", "informatics", "russian".
        type (str): Problem type according to EGE format, e.g., "A", "B", "task_1".
        text (str): Full problem statement, including LaTeX markup.
        options (Optional[List[str]]): Multiple-choice options if applicable. May be null.
        answer (Optional[str]): Canonical answer string; may be null for open-ended or unsolved problems.
        solutions (Optional[List[Dict[str, Any]]]): List of solution dictionaries, each containing fields like
            'solution_id', 'text', 'author'. May be null.
        kes_codes (List[str]): List of KES codes (Content Elements Classifier) identifying curriculum topics,
            e.g., ["1.2.3", "2.1"].
        skills (Optional[List[str]]): List of skill identifiers. May be null.
        difficulty_level (str): Official EGE difficulty level: "basic", "advanced", or "high".
        task_number (int): Position of the problem in the exam paper (1–19).
        kos_codes (List[str]): List of KOS codes (Requirements Classifier) specifying expected competencies.
        exam_part (str): Exam section: "Part 1" or "Part 2".
        max_score (int): Maximum score achievable for this problem (typically 1–4).
        form_id (Optional[str]): Identifier of the answer submission form extracted from FIPI page. May be null.
        source_url (Optional[str]): Original FIPI URL of the problem. May be null.
        raw_html_path (Optional[str]): Path to saved raw HTML file, if preserved. May be null.
        created_at (datetime): ISO8601 timestamp when the record was created.
        updated_at (Optional[datetime]): ISO8601 timestamp of last update. May be null.
        metadata (Optional[Dict[str, Any]]): Arbitrary additional data. May be null.
    """
    problem_id: str
    subject: str
    type: str
    text: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    solutions: Optional[List[Dict[str, Any]]] = None
    kes_codes: List[str] = Field(default_factory=list)
    skills: Optional[List[str]] = None
    difficulty_level: str
    task_number: int
    kos_codes: List[str] = Field(default_factory=list)
    exam_part: str
    max_score: int
    form_id: Optional[str] = None
    source_url: Optional[str] = None
    raw_html_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}
