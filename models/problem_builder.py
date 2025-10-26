"""
Module for building Problem instances from extracted data.

This module provides the `ProblemBuilder` class which encapsulates the logic
for creating and populating `Problem` objects based on parsed HTML content
and extracted metadata.
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
        metadata: Dict[str, Any],
        raw_html_path: Optional[Path] = None,
        # --- Поля, добавленные для соответствия модели Problem ---
        options: Optional[List[str]] = None,
        answer: str = "placeholder_answer", # Пока placeholder, но можно передать
        solutions: Optional[List[Dict[str, Any]]] = None,
        skills: Optional[List[str]] = None,
        updated_at: Optional[datetime] = None,
        # ----------------------------------------------------------
    ) -> Problem:
        """
        Builds a Problem instance from extracted data.

        Args:
            problem_id (str): Unique identifier for the problem.
            subject (str): The subject the problem belongs to.
            type_str (str): The type of the problem.
            text (str): The full text of the problem.
            topics (List[str]): List of KES codes/topics.
            difficulty (str): Estimated difficulty.
            source_url (str): URL of the original problem page.
            metadata (Dict[str, Any]): Additional metadata.
            raw_html_path (Optional[Path]): Path to the original raw HTML file.
            options (Optional[List[str]]): Options for the problem. Defaults to None.
            answer (str): The canonical answer for the problem. Defaults to a placeholder.
            solutions (Optional[List[Dict[str, Any]]]): List of solutions for the problem. Defaults to None.
            skills (Optional[List[str]]): List of skill IDs associated with the problem. Defaults to None.
            updated_at (Optional[datetime]): The last update time for the problem record. Defaults to None.

        Returns:
            Problem: A populated Problem instance.
        """
        logger.debug(f"Building Problem instance for ID: {problem_id} with all fields, including placeholders for optional data.")
        
        # Конвертируем Path в строку, если он предоставлен
        raw_html_path_str = str(raw_html_path) if raw_html_path is not None else None
        
        return Problem(
            problem_id=problem_id,
            subject=subject,
            type=type_str,
            text=text,
            options=options, # Теперь передаётся из аргументов
            answer=answer, # Теперь передаётся из аргументов
            solutions=solutions, # Теперь передаётся из аргументов
            topics=topics,
            skills=skills, # Теперь передаётся из аргументов
            difficulty=difficulty,
            source_url=source_url,
            raw_html_path=raw_html_path_str,
            created_at=datetime.now(),
            updated_at=updated_at, # Теперь передаётся из аргументов
            metadata=metadata
        )
