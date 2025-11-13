# application/factories/problem_factory.py
"""
Фабрика для преобразования Pydantic моделей в Domain модели.
Централизованное место для всех преобразований.
"""

from domain.models.problem import Problem as DomainProblem
from domain.models.problem_schema import Problem as PydanticProblem
from domain.value_objects.problem_id import ProblemId
from domain.value_objects.problem_type import ProblemType, ProblemTypeEnum
from domain.value_objects.difficulty_level import DifficultyLevel, DifficultyLevelEnum
from domain.value_objects.problem_status import ProblemStatus, ProblemStatusEnum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProblemFactory:
    """
    Фабрика для создания Domain Problem из Pydantic Problem.
    
    Business Rules:
    - Работает ТОЛЬКО с существующими enum значениями
    - Безопасная обработка fallback значений
    - Полная поддержка всех полей DomainProblem
    - Четкая обработка ошибок
    """
    
    @staticmethod
    def from_pydantic(pydantic_problem: PydanticProblem) -> DomainProblem:
        """
        Создает Domain Problem из Pydantic Problem.
        
        Args:
            pydantic_problem: Pydantic модель из скрейпинга
            
        Returns:
            DomainProblem: Чистая domain модель с бизнес-логикой
            
        Business Rules:
        - Все обязательные поля DomainProblem должны быть заполнены
        - При ошибках конвертации используем безопасные fallback значения
        - Логируем все проблемы для отладки
        """
        try:
            # 1. Преобразование problem_type с безопасным fallback
            problem_type = ProblemFactory._map_problem_type(pydantic_problem.type)
            
            # 2. Преобразование difficulty_level с безопасным fallback
            difficulty_level = ProblemFactory._map_difficulty_level(pydantic_problem.difficulty_level)
            
            # 3. Default status - DRAFT (обязательное поле в DomainProblem)
            default_status = ProblemStatus(ProblemStatusEnum.DRAFT)
            
            # 4. Безопасная обработка списков
            kes_codes = pydantic_problem.kes_codes or []
            kos_codes = pydantic_problem.kos_codes or []
            options = pydantic_problem.options or []
            
            # 5. Создание Domain Problem
            return DomainProblem(
                problem_id=ProblemId(pydantic_problem.problem_id),
                subject=pydantic_problem.subject,
                problem_type=problem_type,
                text=pydantic_problem.text,
                difficulty_level=difficulty_level,
                exam_part=pydantic_problem.exam_part,
                max_score=pydantic_problem.max_score,
                status=default_status,  # Обязательное поле
                answer=pydantic_problem.answer,
                options=options,
                solutions=pydantic_problem.solutions,
                kes_codes=kes_codes,
                skills=pydantic_problem.skills,
                task_number=pydantic_problem.task_number,
                kos_codes=kos_codes,
                form_id=pydantic_problem.form_id,
                source_url=pydantic_problem.source_url,
                raw_html_path=pydantic_problem.raw_html_path,
                created_at=pydantic_problem.created_at or datetime.now(),
                updated_at=pydantic_problem.updated_at,
                metadata=pydantic_problem.metadata,
                # topics будет установлен в __post_init__ из kes_codes
            )
        except Exception as e:
            logger.error(f"Failed to create domain problem from pydantic data: {e}")
            logger.error(f"Pydantic problem data: {pydantic_problem.dict()}")
            raise ValueError(f"Failed to create domain problem: {e}") from e
    
    @staticmethod
    def _map_problem_type(type_str: str) -> ProblemType:
        """
        Маппинг строкового типа в ProblemType value object.
        
        Business Rules:
        - Используем ТОЛЬКО существующие значения ProblemTypeEnum
        - Безопасный fallback к NUMBER при ошибках
        - Поддержка FIPI форматов
        """
        if not type_str or not isinstance(type_str, str):
            logger.warning(f"Invalid problem type: {type_str}. Using fallback NUMBER.")
            return ProblemType(ProblemTypeEnum.NUMBER)
        
        type_str_clean = type_str.strip().upper()
        
        # Маппинг для FIPI форматов и стандартных типов
        type_mapping = {
            # Стандартные форматы
            "NUMBER": ProblemTypeEnum.NUMBER,
            "TEXT": ProblemTypeEnum.TEXT,
            "MULTIPLE_CHOICE": ProblemTypeEnum.MULTIPLE_CHOICE,
            "MATCHING": ProblemTypeEnum.MATCHING,
            "SHORT_ANSWER": ProblemTypeEnum.SHORT_ANSWER,
            "ESSAY": ProblemTypeEnum.ESSAY,
            
            # FIPI форматы
            "A": ProblemTypeEnum.MULTIPLE_CHOICE,  # Часть A - multiple choice
            "B": ProblemTypeEnum.SHORT_ANSWER,     # Часть B - short answer
            "C": ProblemTypeEnum.ESSAY,            # Часть C - essay
            
            # FIPI task formats
            "TASK_1": ProblemTypeEnum.NUMBER,
            "TASK_2": ProblemTypeEnum.MULTIPLE_CHOICE,
            "TASK_3": ProblemTypeEnum.MULTIPLE_CHOICE,
            "TASK_4": ProblemTypeEnum.MATCHING,
            "TASK_5": ProblemTypeEnum.SHORT_ANSWER,
            "TASK_6": ProblemTypeEnum.ESSAY,
            "TASK_7": ProblemTypeEnum.SHORT_ANSWER,
            "TASK_8": ProblemTypeEnum.MULTIPLE_CHOICE,
            "TASK_9": ProblemTypeEnum.NUMBER,
            "TASK_10": ProblemTypeEnum.MATCHING,
            "TASK_11": ProblemTypeEnum.SHORT_ANSWER,
            "TASK_12": ProblemTypeEnum.ESSAY,
            "TASK_13": ProblemTypeEnum.NUMBER,
            "TASK_14": ProblemTypeEnum.MATCHING,
            "TASK_15": ProblemTypeEnum.SHORT_ANSWER,
            "TASK_16": ProblemTypeEnum.ESSAY,
            "TASK_17": ProblemTypeEnum.NUMBER,
            "TASK_18": ProblemTypeEnum.MATCHING,
            "TASK_19": ProblemTypeEnum.SHORT_ANSWER,
            
            # Синонимы и опечатки
            "MULTI_CHOICE": ProblemTypeEnum.MULTIPLE_CHOICE,
            "MULTIPLE": ProblemTypeEnum.MULTIPLE_CHOICE,
            "CHOICE": ProblemTypeEnum.MULTIPLE_CHOICE,
            "SHORT": ProblemTypeEnum.SHORT_ANSWER,
            "LONG": ProblemTypeEnum.ESSAY,
            "MATCH": ProblemTypeEnum.MATCHING,
        }
        
        # Ищем точное совпадение
        if type_str_clean in type_mapping:
            return ProblemType(type_mapping[type_str_clean])
        
        # Попытка найти по частичному совпадению
        for key, value in type_mapping.items():
            if key in type_str_clean or type_str_clean in key:
                logger.warning(f"Partial match for problem type: '{type_str_clean}' -> '{key}'")
                return ProblemType(value)
        
        # Безопасный fallback
        logger.warning(f"Unknown problem type: '{type_str_clean}'. Using fallback NUMBER.")
        return ProblemType(ProblemTypeEnum.NUMBER)
    
    @staticmethod
    def _map_difficulty_level(level_str: str) -> DifficultyLevel:
        """
        Маппинг строкового уровня сложности в DifficultyLevel value object.
        
        Business Rules:
        - Используем ТОЛЬКО существующие значения DifficultyLevelEnum
        - Безопасный fallback к BASIC при ошибках
        - Поддержка русских и английских названий
        """
        if not level_str or not isinstance(level_str, str):
            logger.warning(f"Invalid difficulty level: {level_str}. Using fallback BASIC.")
            return DifficultyLevel(DifficultyLevelEnum.BASIC)
        
        level_str_clean = level_str.strip().lower()
        
        # Маппинг для разных форматов
        level_mapping = {
            # Английские названия
            "basic": DifficultyLevelEnum.BASIC,
            "easy": DifficultyLevelEnum.BASIC,
            "simple": DifficultyLevelEnum.BASIC,
            "low": DifficultyLevelEnum.BASIC,
            
            "intermediate": DifficultyLevelEnum.INTERMEDIATE,
            "medium": DifficultyLevelEnum.INTERMEDIATE,
            "normal": DifficultyLevelEnum.INTERMEDIATE,
            "mid": DifficultyLevelEnum.INTERMEDIATE,
            
            "advanced": DifficultyLevelEnum.ADVANCED,
            "hard": DifficultyLevelEnum.ADVANCED,
            "difficult": DifficultyLevelEnum.ADVANCED,
            "high": DifficultyLevelEnum.ADVANCED,
            "complex": DifficultyLevelEnum.ADVANCED,
            
            # Русские названия
            "низкий": DifficultyLevelEnum.BASIC,
            "легкий": DifficultyLevelEnum.BASIC,
            "простой": DifficultyLevelEnum.BASIC,
            
            "средний": DifficultyLevelEnum.INTERMEDIATE,
            "обычный": DifficultyLevelEnum.INTERMEDIATE,
            
            "высокий": DifficultyLevelEnum.ADVANCED,
            "сложный": DifficultyLevelEnum.ADVANCED,
            "трудный": DifficultyLevelEnum.ADVANCED,
            
            # FIPI форматы
            "базовый": DifficultyLevelEnum.BASIC,
            "повышенный": DifficultyLevelEnum.INTERMEDIATE,
            "высокий": DifficultyLevelEnum.ADVANCED,
        }
        
        # Точное совпадение
        if level_str_clean in level_mapping:
            return DifficultyLevel(level_mapping[level_str_clean])
        
        # Частичное совпадение
        for key, value in level_mapping.items():
            if key in level_str_clean or level_str_clean in key:
                logger.warning(f"Partial match for difficulty level: '{level_str_clean}' -> '{key}'")
                return DifficultyLevel(value)
        
        # Безопасный fallback
        logger.warning(f"Unknown difficulty level: '{level_str_clean}'. Using fallback BASIC.")
        return DifficultyLevel(DifficultyLevelEnum.BASIC)