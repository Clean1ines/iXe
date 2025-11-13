# tests/unit/application/factories/test_problem_factory.py
"""
Unit tests for ProblemFactory - critical component of the architecture.
Tests ensure proper conversion from Pydantic to Domain models.
"""

import pytest
from datetime import datetime
from unittest.mock import patch
import logging

from domain.models.problem_schema import Problem as PydanticProblem
from application.factories.problem_factory import ProblemFactory
from domain.value_objects.problem_type import ProblemTypeEnum
from domain.value_objects.difficulty_level import DifficultyLevelEnum
from domain.value_objects.problem_status import ProblemStatusEnum

# Настройка логгера для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_factory_creates_domain_problem():
    """Тест: успешное создание domain проблемы из pydantic"""
    # Arrange
    pydantic_problem = PydanticProblem(
        problem_id="math_1_2025_1",
        subject="mathematics",
        type="TASK_1",  # FIPI формат
        text="Solve: 2 + 2 = ?",
        difficulty_level="basic",
        exam_part="Part 1",
        max_score=1,
        task_number=1,
        kes_codes=["1.1", "1.2"],
        kos_codes=["2.1"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        # Остальные поля по умолчанию
    )
    
    # Act
    domain_problem = ProblemFactory.from_pydantic(pydantic_problem)
    
    # Assert
    assert domain_problem.problem_id.value == "math_1_2025_1"
    assert domain_problem.subject == "mathematics"
    assert domain_problem.problem_type.value == ProblemTypeEnum.NUMBER
    assert domain_problem.difficulty_level.value == DifficultyLevelEnum.BASIC
    assert domain_problem.exam_part == "Part 1"
    assert domain_problem.max_score == 1
    assert domain_problem.task_number == 1
    assert domain_problem.kes_codes == ["1.1", "1.2"]
    assert domain_problem.status.value == ProblemStatusEnum.DRAFT
    assert domain_problem.created_at is not None
    assert domain_problem.updated_at is not None

def test_factory_handles_unknown_problem_type():
    """Тест: обработка неизвестного типа проблемы с fallback"""
    # Arrange
    pydantic_problem = PydanticProblem(
        problem_id="math_2_2025_1",
        subject="mathematics",
        type="UNKNOWN_TYPE",  # Неизвестный тип
        text="What is the capital of France?",
        difficulty_level="intermediate",
        exam_part="Part 1",
        max_score=1,
        task_number=2,
        kes_codes=[],
        kos_codes=[],
        created_at=datetime.now()
    )
    
    # Act & Assert
    domain_problem = ProblemFactory.from_pydantic(pydantic_problem)
    
    # Должен использовать fallback NUMBER
    assert domain_problem.problem_type.value == ProblemTypeEnum.NUMBER
    logger.info("Successfully handled unknown problem type with fallback")

def test_factory_handles_russian_difficulty_level():
    """Тест: обработка русского уровня сложности"""
    # Arrange
    pydantic_problem = PydanticProblem(
        problem_id="rus_3_2025_1",
        subject="russian",
        type="TASK_3",
        text="Найдите ошибку в предложении.",
        difficulty_level="средний",  # Русский язык
        exam_part="Part 1",
        max_score=1,
        task_number=3,
        kes_codes=["3.1"],
        kos_codes=["4.2"],
        created_at=datetime.now()
    )
    
    # Act
    domain_problem = ProblemFactory.from_pydantic(pydantic_problem)
    
    # Assert
    assert domain_problem.difficulty_level.value == DifficultyLevelEnum.INTERMEDIATE
    logger.info("Successfully mapped russian difficulty level")

def test_factory_handles_missing_optional_fields():
    """Тест: обработка отсутствующих опциональных полей"""
    # Arrange
    pydantic_problem = PydanticProblem(
        problem_id="physics_4_2025_1",
        subject="physics",
        type="TASK_4",
        text="Calculate the force.",
        difficulty_level="advanced",
        exam_part="Part 2",
        max_score=2,
        task_number=4,
        kes_codes=[],
        kos_codes=[],
        created_at=datetime.now()
        # Все опциональные поля отсутствуют
    )
    
    # Act
    domain_problem = ProblemFactory.from_pydantic(pydantic_problem)
    
    # Assert
    assert domain_problem.answer is None
    assert domain_problem.options == []  # Пустой список по умолчанию
    assert domain_problem.solutions is None
    assert domain_problem.skills is None
    assert domain_problem.form_id is None
    assert domain_problem.source_url is None
    assert domain_problem.raw_html_path is None
    assert domain_problem.metadata is None
    logger.info("Successfully handled missing optional fields")

def test_factory_handles_invalid_business_data_gracefully():
    """
    Тест: graceful обработка невалидных бизнес-данных
    
    Важно: PydanticProblem сам по себе валидирует типы, поэтому мы создаем
    валидную Pydantic модель, но с данными, которые вызовут ошибки бизнес-валидации
    в DomainProblem.
    """
    # Arrange - создаем ВАЛИДНУЮ Pydantic модель с НЕВАЛИДНЫМИ бизнес-данными
    pydantic_problem = PydanticProblem(
        problem_id="invalid_1_2025_1",
        subject="",  # Пустой предмет - валидная строка для Pydantic, но невалидная для бизнес-логики
        type="TASK_1",  # Валидный тип
        text="Invalid problem data",
        difficulty_level="basic",  # Валидный уровень
        exam_part="Invalid Part",  # Невалидная часть экзамена
        max_score=-1,  # Отрицательный балл - валидное число для Pydantic
        task_number=20,  # Невалидный номер задачи
        kes_codes=["1.1"],
        kos_codes=["2.1"],
        created_at=datetime.now()
    )
    
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        ProblemFactory.from_pydantic(pydantic_problem)
    
    # Проверяем, что ошибка содержит информацию о бизнес-валидации
    error_str = str(exc_info.value)
    assert "Failed to create domain problem" in error_str
    assert any(validation_error in error_str for validation_error in [
        "Subject cannot be empty",
        "Exam part must be either 'Part 1' or 'Part 2'",
        "Max score must be positive",
        "Task number must be between 1 and 19"
    ])
    
    logger.info("Successfully handled invalid business data with proper validation error")