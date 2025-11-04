"""
Module for building Problem instances from extracted data.

This module provides the `ProblemBuilder` class which encapsulates the logic
for creating and populating `Problem` objects based on parsed HTML content
and extracted metadata, using the current minimal Problem schema.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from models.problem_schema import Problem

logger = logging.getLogger(__name__)


class ProblemBuilder:
    """
    A class responsible for constructing Problem instances from raw data.
    """

    def build(
        self,
        problem_id: str,
        subject: str,
        type_str: str,
        text: str,
        topics: List[str],
        source_url: str,
        form_id: Optional[str],
        meta: Dict[str, Any],
        task_number: int,
        kes_codes: List[str],
        kos_codes: List[str],
        exam_part: str,
        max_score: int,
        difficulty_level: str,
        answer: Optional[str] = None,
        options: Optional[List[str]] = None,
        updated_at: Optional[datetime] = None,
    ) -> Problem:
        """
        Builds a Problem instance from extracted data.

        Args:
            problem_id: Unique identifier for the problem (e.g., "init_40B442").
            subject: The subject (e.g., "mathematics").
            type_str: The type of the problem (e.g., "short", "extended").
            text: The full text of the problem.
            topics: List of KES codes (synonym for kes_codes).
            source_url: URL of the original problem page.
            form_id: The form ID for answer submission (from qblock id).
            meta: Additional metadata (e.g., original_block_index).
            task_number: The official ЕГЭ task number (1-19).
            kes_codes: List of KES codes.
            kos_codes: List of KOS codes.
            exam_part: "Part 1" or "Part 2".
            max_score: Maximum score for the task.
            difficulty_level: "basic", "advanced", or "high".
            answer: The canonical answer (None until verified).
            options: Options for multiple-choice problems.
            updated_at: Timestamp of last update.

        Returns:
            A populated Problem instance.
        """
        logger.debug(f"Building Problem instance for ID: {problem_id}")
        
        return Problem(
            problem_id=problem_id,
            subject=subject,
            type=type_str,
            text=text,
            options=options,
            answer=answer,
            topics=topics,
            difficulty_level=difficulty_level,
            kes_codes=kes_codes,
            kos_codes=kos_codes,
            exam_part=exam_part,
            max_score=max_score,
            form_id=form_id,
            source_url=source_url,
            created_at=datetime.now(),
            updated_at=updated_at,
            task_number=task_number
        )
