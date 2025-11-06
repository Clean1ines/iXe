"""
Common package for the EGE prep platform.

This package contains shared models, utilities, and services
used across the scraper-service and checker-service.
"""

# Re-export key models and utilities for easier imports
from .models.problem_schema import Problem
from .models.check_answer_schema import CheckAnswerRequest, CheckAnswerResponse
from .models.database_models import Base, DBProblem, DBAnswer
from .utils.database_manager import DatabaseManager, DatabaseBackend, SQLDatabaseBackend
from .utils.task_id_utils import extract_task_id_and_form_id
from .utils.task_number_inferer import TaskNumberInferer
from .utils.model_adapter import db_problem_to_problem
from .utils.subject_mapping import (
    SUBJECT_ALIAS_MAP,
    SUBJECT_KEY_MAP,
    SUBJECT_TO_PROJ_ID_MAP,
    SUBJECT_TO_OFFICIAL_NAME_MAP,
    get_alias_from_official_name,
    get_subject_key_from_alias,
    get_proj_id_for_subject,
    get_official_name_from_alias
)
from .utils.fipi_urls import (
    FIPI_BASE_URL,
    FIPI_SUBJECTS_LIST_URL,
    FIPI_QUESTIONS_URL,
    FIPI_BANK_ROOT_URL
)

# Define what gets imported with "from common import *"
__all__ = [
    # Models
    "Problem",
    "CheckAnswerRequest",
    "CheckAnswerResponse",
    "Base",
    "DBProblem",
    "DBAnswer",
    # Managers/Backends
    "DatabaseManager",
    "DatabaseBackend",
    "SQLDatabaseBackend",
    # Utils
    "extract_task_id_and_form_id",
    "TaskNumberInferer",
    "db_problem_to_problem",
    # Subject mapping
    "SUBJECT_ALIAS_MAP",
    "SUBJECT_KEY_MAP",
    "SUBJECT_TO_PROJ_ID_MAP",
    "SUBJECT_TO_OFFICIAL_NAME_MAP",
    "get_alias_from_official_name",
    "get_subject_key_from_alias",
    "get_proj_id_for_subject",
    "get_official_name_from_alias",
    # URLs
    "FIPI_BASE_URL",
    "FIPI_SUBJECTS_LIST_URL",
    "FIPI_QUESTIONS_URL",
    "FIPI_BANK_ROOT_URL",
]

