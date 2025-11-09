# domain/models/__init__.py
# Экспорт всех моделей для удобного импорта

from .problem_schema import Problem
from .database_models import DBProblem, DBAnswer
from .problem_builder import ProblemBuilder

# Если AnswerCheckResult и UserAnswer находятся в другом месте, импортируем их оттуда
try:
    from domain.models.answer_schema import AnswerCheckResult, UserAnswer
except ImportError:
    # Временное решение - создаем минимальные версии для совместимости
    class AnswerCheckResult:
        pass
    
    class UserAnswer:
        pass
