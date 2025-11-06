"""
Utils subpackage for the common package.

Contains utility functions and classes.
"""

from .database_manager import DatabaseManager, DatabaseBackend, SQLDatabaseBackend
from .task_id_utils import extract_task_id_and_form_id
from .task_number_inferer import TaskNumberInferer
from .model_adapter import db_problem_to_problem
from .subject_mapping import (
    SUBJECT_ALIAS_MAP,
    SUBJECT_KEY_MAP,
    SUBJECT_TO_PROJ_ID_MAP,
    SUBJECT_TO_OFFICIAL_NAME_MAP,
    get_alias_from_official_name,
    get_subject_key_from_alias,
    get_proj_id_for_subject,
    get_official_name_from_alias
)
from .fipi_urls import (
    FIPI_BASE_URL,
    FIPI_SUBJECTS_LIST_URL,
    FIPI_QUESTIONS_URL,
    FIPI_BANK_ROOT_URL
)

__all__ = [
    "DatabaseManager",
    "DatabaseBackend", 
    "SQLDatabaseBackend",
    "extract_task_id_and_form_id",
    "TaskNumberInferer",
    "db_problem_to_problem",
    "SUBJECT_ALIAS_MAP",
    "SUBJECT_KEY_MAP",
    "SUBJECT_TO_PROJ_ID_MAP",
    "SUBJECT_TO_OFFICIAL_NAME_MAP",
    "get_alias_from_official_name",
    "get_subject_key_from_alias",
    "get_proj_id_for_subject",
    "get_official_name_from_alias",
    "FIPI_BASE_URL",
    "FIPI_SUBJECTS_LIST_URL",
    "FIPI_QUESTIONS_URL",
    "FIPI_BANK_ROOT_URL",
]

