"""
Module for safely converting between SQLAlchemy models and Pydantic models.
Provides adapter functions that handle attribute mismatches gracefully.
"""
import logging
from typing import Any, Dict, Optional
from models.problem_schema import Problem
from models.database_models import DBProblem

logger = logging.getLogger(__name__)

def safe_getattr(obj: Any, *attrs: str, default: Any = None) -> Any:
    """
    Safely get an attribute from an object, trying multiple attribute names.
    Returns the first found attribute or the default value.
    
    Args:
        obj: Object to get attribute from
        *attrs: Attribute names to try in order
        default: Default value if no attribute is found
    
    Returns:
        The value of the first found attribute or default
    """
    for attr in attrs:
        if hasattr(obj, attr):
            return getattr(obj, attr)
    return default

def convert_to_dict(obj: Any) -> Optional[Dict]:
    """
    Attempt to convert an object to a dictionary.
    Returns None if conversion is not possible.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
        return obj.dict()
    if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
        return obj.to_dict()
    if hasattr(obj, '__dict__'):
        return vars(obj)
    
    logger.warning(f"Could not convert object of type {type(obj)} to dictionary")
    return None

def db_problem_to_problem(db_problem: DBProblem) -> Problem:
    """
    Convert a DBProblem SQLAlchemy model to a Pydantic Problem model.
    Handles attribute mismatches safely.
    """
    # Handle metadata conversion specifically
    raw_metadata = safe_getattr(db_problem, 'metadata_', 'metadata', default=None)
    metadata_dict = convert_to_dict(raw_metadata)
    
    # Ensure metadata is a dict or None
    if not isinstance(metadata_dict, dict) and metadata_dict is not None:
        metadata_dict = None
    
    # Handle solutions with safe_getattr
    solutions = safe_getattr(db_problem, 'solutions', 'solution', default=None)
    
    # Handle skills with safe_getattr
    skills = safe_getattr(db_problem, 'skills', 'skill_codes', default=None)
    
    # Handle topics/kes_codes
    kes_codes = safe_getattr(db_problem, 'kes_codes', 'topics', default=[])
    if kes_codes is None:
        kes_codes = []
    
    # Handle kos_codes
    kos_codes = safe_getattr(db_problem, 'kos_codes', 'requirements', default=[])
    if kos_codes is None:
        kos_codes = []
    
    # Handle exam_part with fallback
    exam_part = safe_getattr(db_problem, 'exam_part', 'part', default='Part 1')
    
    # Handle max_score with fallback
    max_score = safe_getattr(db_problem, 'max_score', 'score', default=1)
    
    # Handle form_id with fallback
    form_id = safe_getattr(db_problem, 'form_id', 'form', default=None)
    
    # Handle updated_at with fallback
    updated_at = safe_getattr(db_problem, 'updated_at', 'modified_at', default=None)
    
    return Problem(
        problem_id=db_problem.problem_id,
        subject=db_problem.subject,
        type=db_problem.type,
        text=db_problem.text,
        options=db_problem.options,
        answer=db_problem.answer,
        solutions=solutions,
        topics=kes_codes,
        skills=skills,
        difficulty_level=safe_getattr(db_problem, 'difficulty_level', 'difficulty', default='basic'),
        task_number=db_problem.task_number,
        kes_codes=kes_codes,
        kos_codes=kos_codes,
        exam_part=exam_part,
        max_score=max_score,
        form_id=form_id,
        source_url=db_problem.source_url,
        raw_html_path=db_problem.raw_html_path,
        created_at=db_problem.created_at,
        updated_at=updated_at,
        metadata=metadata_dict,  # Now properly converted to dict or None
    )
