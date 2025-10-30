# api/dependencies.py
from fastapi import Depends, HTTPException
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from api.services.quiz_service import QuizService
from api.services.answer_service import AnswerService
from config import DB_PATH, USE_LOCAL_STORAGE, FIPI_QUESTIONS_URL, is_stateless

def get_db_manager() -> DatabaseManager:
    """
    Dependency to provide an instance of DatabaseManager.

    Returns:
        DatabaseManager: An instance of the database manager.
    """
    return DatabaseManager(DB_PATH)

# --- Зависимости для сервисов ---
def get_storage() -> LocalStorage | None:
    """
    Dependency to provide an instance of LocalStorage or None.

    Returns:
        LocalStorage | None: An instance of local storage if enabled and not stateless, otherwise None.
    """
    if USE_LOCAL_STORAGE and not is_stateless(): # Не использовать storage в stateless режиме
        return LocalStorage("answers.json")
    return None

def get_answer_checker() -> FIPIAnswerChecker:
    """
    Dependency to provide an instance of FIPIAnswerChecker.

    Returns:
        FIPIAnswerChecker: An instance of the answer checker.
    """
    return FIPIAnswerChecker(base_url=FIPI_QUESTIONS_URL)

# --- Сервисы ---
def get_quiz_service(db: DatabaseManager = Depends(get_db_manager)) -> QuizService:
    """
    Dependency to provide an instance of QuizService.

    Args:
        db: The database manager instance.

    Returns:
        QuizService: An instance of the quiz service.
    """
    return QuizService(db)

def get_answer_service(
    db: DatabaseManager = Depends(get_db_manager),
    checker: FIPIAnswerChecker = Depends(get_answer_checker),
    storage: LocalStorage | None = Depends(get_storage)
) -> AnswerService:
    """
    Dependency to provide an instance of AnswerService.

    Args:
        db: The database manager instance.
        checker: The answer checker instance.
        storage: Optional local storage instance.

    Returns:
        AnswerService: An instance of the answer service.
    """
    return AnswerService(db, checker, storage)
