"""
Module for safely converting between SQLAlchemy models and domain entities.
Provides adapter functions that handle attribute mismatches gracefully
and maintain compatibility between domain models and infrastructure models.
"""
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime
from domain.models.problem import Problem as DomainProblem
from domain.models.user_progress import UserProgress as DomainUserProgress
from domain.models.skill import Skill as DomainSkill
from domain.value_objects.problem_id import ProblemId
from domain.value_objects.difficulty_level import DifficultyLevel, DifficultyLevelEnum
from domain.value_objects.problem_type import ProblemType, ProblemTypeEnum
from domain.models.database_models import DBProblem, DBUserProgress, DBSkill
from domain.models.problem_schema import Problem as PydanticProblem


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

def domain_to_db_problem(domain_problem: DomainProblem) -> DBProblem:
    """
    Convert a domain Problem entity to a SQLAlchemy DBProblem model.
    
    Args:
        domain_problem: The domain problem entity to convert
        
    Returns:
        The corresponding database model
    """
    # Convert value objects back to their primitive types
    problem_id_str = str(domain_problem.problem_id)
    difficulty_str = str(domain_problem.difficulty_level)
    type_str = str(domain_problem.problem_type)
    
    return DBProblem(
        problem_id=problem_id_str,
        subject=domain_problem.subject,
        type=type_str,
        text=domain_problem.text,
        options=domain_problem.options,
        answer=domain_problem.answer,
        solutions=domain_problem.solutions,
        kes_codes=domain_problem.kes_codes,
        skills=domain_problem.skills,
        difficulty_level=difficulty_str,
        task_number=domain_problem.task_number,
        kos_codes=domain_problem.kos_codes,
        exam_part=domain_problem.exam_part,
        max_score=domain_problem.max_score,
        form_id=domain_problem.form_id,
        source_url=domain_problem.source_url,
        raw_html_path=domain_problem.raw_html_path,
        created_at=domain_problem.created_at,
        updated_at=domain_problem.updated_at,
        metadata_=domain_problem.metadata,
    )

def db_to_domain_problem(db_problem: DBProblem) -> DomainProblem:
    """
    Convert a DBProblem SQLAlchemy model to a domain Problem entity.
    
    Args:
        db_problem: The database model to convert
        
    Returns:
        The corresponding domain entity
    """
    # Create value objects from primitive types
    problem_id = ProblemId(value=db_problem.problem_id)
    difficulty_level = DifficultyLevel(value=DifficultyLevelEnum(db_problem.difficulty_level))
    problem_type = ProblemType(value=ProblemTypeEnum(db_problem.type))
    
    return DomainProblem(
        problem_id=problem_id,
        subject=db_problem.subject,
        problem_type=problem_type,
        text=db_problem.text,
        difficulty_level=difficulty_level,
        exam_part=db_problem.exam_part,
        max_score=db_problem.max_score,
        answer=db_problem.answer,
        options=db_problem.options,
        solutions=db_problem.solutions,
        kes_codes=db_problem.kes_codes,
        skills=db_problem.skills,
        task_number=db_problem.task_number,
        kos_codes=db_problem.kos_codes,
        form_id=db_problem.form_id,
        source_url=db_problem.source_url,
        raw_html_path=db_problem.raw_html_path,
        created_at=db_problem.created_at or datetime.now(),
        updated_at=db_problem.updated_at,
        metadata=db_problem.metadata_,
    )

def pydantic_to_domain_problem(pydantic_problem: PydanticProblem) -> DomainProblem:
    """
    Convert a Pydantic Problem model to a domain Problem entity.
    
    Args:
        pydantic_problem: The Pydantic problem model to convert
        
    Returns:
        The corresponding domain entity
    """
    # Create value objects from primitive types
    problem_id = ProblemId(value=pydantic_problem.problem_id)
    difficulty_level = DifficultyLevel(value=DifficultyLevelEnum(pydantic_problem.difficulty_level))
    problem_type = ProblemType(value=ProblemTypeEnum(pydantic_problem.type))
    
    return DomainProblem(
        problem_id=problem_id,
        subject=pydantic_problem.subject,
        problem_type=problem_type,
        text=pydantic_problem.text,
        difficulty_level=difficulty_level,
        exam_part=pydantic_problem.exam_part,
        max_score=pydantic_problem.max_score,
        answer=pydantic_problem.answer,
        options=pydantic_problem.options,
        solutions=pydantic_problem.solutions,
        kes_codes=pydantic_problem.kes_codes,
        skills=pydantic_problem.skills,
        task_number=pydantic_problem.task_number,
        kos_codes=pydantic_problem.kos_codes,
        form_id=pydantic_problem.form_id,
        source_url=pydantic_problem.source_url,
        raw_html_path=pydantic_problem.raw_html_path,
        created_at=pydantic_problem.created_at,
        updated_at=pydantic_problem.updated_at,
        metadata=pydantic_problem.metadata,
    )

def domain_to_db_user_progress(domain_progress: DomainUserProgress) -> DBUserProgress:
    """
    Convert a domain UserProgress entity to a SQLAlchemy DBUserProgress model.
    
    Args:
        domain_progress: The domain user progress entity to convert
        
    Returns:
        The corresponding database model
    """
    problem_id_str = str(domain_progress.problem_id)
    
    return DBUserProgress(
        user_id=domain_progress.user_id,
        problem_id=problem_id_str,
        status=domain_progress.status.value,
        score=domain_progress.score,
        attempts=domain_progress.attempts,
        last_attempt_at=domain_progress.last_attempt_at,
        started_at=domain_progress.started_at,
    )

def db_to_domain_user_progress(db_progress: DBUserProgress) -> DomainUserProgress:
    """
    Convert a DBUserProgress SQLAlchemy model to a domain UserProgress entity.
    
    Args:
        db_progress: The database model to convert
        
    Returns:
        The corresponding domain entity
    """
    problem_id = ProblemId(value=db_progress.problem_id)
    
    from domain.models.user_progress import ProgressStatus
    status_enum = ProgressStatus(db_progress.status)
    
    return DomainUserProgress(
        user_id=db_progress.user_id,
        problem_id=problem_id,
        status=status_enum,
        score=db_progress.score,
        attempts=db_progress.attempts,
        last_attempt_at=db_progress.last_attempt_at,
        started_at=db_progress.started_at,
    )

def domain_to_db_skill(domain_skill: DomainSkill) -> DBSkill:
    """
    Convert a domain Skill entity to a SQLAlchemy DBSkill model.
    
    Args:
        domain_skill: The domain skill entity to convert
        
    Returns:
        The corresponding database model
    """
    # Convert ProblemId list to string list
    problem_ids_str = [str(pid) for pid in domain_skill.related_problems]
    
    return DBSkill(
        skill_id=domain_skill.skill_id,
        name=domain_skill.name,
        description=domain_skill.description,
        prerequisites=domain_skill.prerequisites,
        related_problems=problem_ids_str,
    )

def db_to_domain_skill(db_skill: DBSkill) -> DomainSkill:
    """
    Convert a DBSkill SQLAlchemy model to a domain Skill entity.
    
    Args:
        db_skill: The database model to convert
        
    Returns:
        The corresponding domain entity
    """
    # Convert string list to ProblemId list
    problem_ids = [ProblemId(value=pid_str) for pid_str in db_skill.related_problems]
    
    return DomainSkill(
        skill_id=db_skill.skill_id,
        name=db_skill.name,
        description=db_skill.description,
        prerequisites=db_skill.prerequisites,
        related_problems=problem_ids,
    )

def db_problem_to_problem(db_problem: DBProblem) -> PydanticProblem:
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
    
    return PydanticProblem(
        problem_id=db_problem.problem_id,
        subject=db_problem.subject,
        type=db_problem.type,
        text=db_problem.text,
        options=db_problem.options,
        answer=db_problem.answer,
        solutions=solutions,
        kes_codes=kes_codes,
        skills=skills,
        difficulty_level=safe_getattr(db_problem, 'difficulty_level', 'difficulty', default='basic'),
        task_number=db_problem.task_number,
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
