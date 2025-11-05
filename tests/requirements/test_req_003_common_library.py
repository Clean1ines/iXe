"""
Тесты для проверки архитектурного требования REQ-003.
Проверяют, что общие компоненты импортируются из common и что дубликатов нет.
"""
import pytest
import importlib
import sys
import os

# Пути, где не должны находиться файлы, перенесённые в common
FORBIDDEN_PATHS = [
    "models/database_models.py", # Перенесён в common.models.database_models
    "models/problem_schema.py",  # Перенесён в common.models.problem_schema
    "utils/model_adapter.py",    # Перенесён в common.utils.model_adapter
    "utils/subject_mapping.py",  # Перенесён в common.utils.subject_mapping
    "utils/task_id_utils.py",    # Перенесён в common.utils.task_id_utils
    "utils/task_number_inferer.py", # Перенесён в common.utils.task_number_inferer
    "utils/fipi_urls.py",        # Перенесён в common.utils.fipi_urls
    "processors/page_processor.py", # Перенесён в common.processors.page_processor
    "processors/block_processor.py", # Перенесён в common.processors.block_processor
    "services/specification.py", # Перенесён в common.services.specification
    # Добавьте сюда другие пути, если были перенесены
]

def test_common_components_importable():
    """Проверяет, что компоненты из common можно импортировать."""
    # Примеры импортов из common
    try:
        from common.models.database_models import DBProblem, DBAnswer
        from common.models.problem_schema import Problem
        from common.utils.model_adapter import db_problem_to_problem
        from common.utils.subject_mapping import SUBJECT_KEY_MAP
        from common.utils.task_id_utils import extract_task_id_and_form_id
        from common.utils.task_number_inferer import TaskNumberInferer
        from common.utils.fipi_urls import FIPI_QUESTIONS_URL
        from common.services.specification import SpecificationService
    except ImportError as e:
        pytest.fail(f"Не удалось импортировать компонент из common: {e}")

    # Проверим, что импортированные объекты существуют
    assert DBProblem is not None
    assert DBAnswer is not None
    assert Problem is not None
    assert callable(db_problem_to_problem)
    assert SUBJECT_KEY_MAP is not None
    assert callable(extract_task_id_and_form_id)
    assert callable(TaskNumberInferer)
    assert FIPI_QUESTIONS_URL is not None
    assert callable(SpecificationService)

def test_no_duplicate_implementations():
    """Проверяет, что старые файлы, перенесённые в common, больше не существуют."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ../ от tests/
    for path in FORBIDDEN_PATHS:
        full_path = os.path.join(base_path, path)
        if os.path.exists(full_path):
            pytest.fail(f"Старая реализация найдена по пути: {full_path}")
