"""
Module for building Problem instances from extracted data.

This module provides the `ProblemBuilder` class which encapsulates the logic
for creating and populating `Problem` objects based on parsed HTML content
and extracted metadata, including extended fields for task_number, codes, and exam details.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from models.problem_schema import Problem

logger = logging.getLogger(__name__)


class ProblemBuilder:
    """
    A class responsible for constructing Problem instances from raw data.

    This builder takes extracted information such as text, type, difficulty,
    and metadata, and uses it to create a well-formed `Problem` object.
    """

    def build(
        self,
        problem_id: str,
        subject: str,
        type_str: str,
        text: str,
        topics: List[str],
        difficulty: str,
        source_url: str,
        meta: Dict[str, Any],
        form_id: Optional[str] = None, # Сделано опциональным
        raw_html_path: Optional[Path] = None,
        # --- Поля, добавленные для соответствия модели Problem ---
        options: Optional[List[str]] = None,
        answer: str = "placeholder_answer", # Пока placeholder, но можно передать
        solutions: Optional[List[Dict[str, Any]]] = None,
        skills: Optional[List[str]] = None,
        updated_at: Optional[datetime] = None,
        # ----------------------------------------------------------
        # --- Новые поля для расширенной модели ---
        task_number: Optional[int] = None,
        kes_codes: Optional[List[str]] = None,
        kos_codes: Optional[List[str]] = None,
        exam_part: Optional[str] = None,
        max_score: Optional[int] = None,
        difficulty_level: Optional[str] = None,
    ) -> Problem:
        """
        Builds a Problem instance from extracted data with extended metadata fields.

        Args:
            problem_id (str): Unique identifier for the problem.
            subject (str): The subject the problem belongs to.
            type_str (str): The type of the problem.
            text (str): The full text of the problem.
            topics (List[str]): List of KES codes/topics.
            difficulty (str): Estimated difficulty (deprecated, use difficulty_level).
            source_url (str): URL of the original problem page.
            meta (Dict[str, Any]): Additional metadata.
            form_id (Optional[str]): The form ID for answer submission. Can be None if no form exists.
            raw_html_path (Optional[Path]): Path to the original raw HTML file.
            options (Optional[List[str]]): Options for the problem. Defaults to None.
            answer (str): The canonical answer for the problem. Defaults to a placeholder.
            solutions (Optional[List[Dict[str, Any]]]): List of solutions for the problem. Defaults to None.
            skills (Optional[List[str]]): List of skill IDs associated with the problem. Defaults to None.
            updated_at (Optional[datetime]): The last update time for the problem record. Defaults to None.
            task_number (Optional[int]): The sequential number of the task in the exam.
            kes_codes (Optional[List[str]]): List of KES codes for the problem.
            kos_codes (Optional[List[str]]): List of KOS codes for the problem.
            exam_part (Optional[str]): The part of the exam the task belongs to (e.g., part1, part2).
            max_score (Optional[int]): The maximum score possible for this task.
            difficulty_level (Optional[str]): The difficulty level of the task (e.g., easy, medium, hard).

        Returns:
            Problem: A populated Problem instance with all extended fields.
        """
        logger.debug(f"Building Problem instance for ID: {problem_id} with all fields, including extended metadata.")
        
        # Конвертируем Path в строку, если он предоставлен
        raw_html_path_str = str(raw_html_path) if raw_html_path is not None else None
        
        # Use difficulty as fallback for difficulty_level if not provided
        if difficulty_level is None:
            difficulty_level = difficulty
        
        # Use topics as fallback for kes_codes if not provided
        if kes_codes is None:
            kes_codes = topics
        
        return Problem(
            problem_id=problem_id,
            subject=subject,
            type=type_str,
            text=text,
            options=options,
            answer=answer,
            solutions=solutions,
            topics=topics,
            skills=skills,
            difficulty=difficulty_level,  # Use the new difficulty_level field in the model
            source_url=source_url,
            form_id=form_id, # Передаём form_id (может быть None)
            raw_html_path=raw_html_path_str,
            created_at=datetime.now(),
            updated_at=updated_at,
            metadata=meta,
            task_number=task_number,
            kes_codes=kes_codes,
            kos_codes=kos_codes,
            exam_part=exam_part,
            max_score=max_score,
            difficulty_level=difficulty_level
        )

