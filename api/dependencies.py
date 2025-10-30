# api/dependencies.py
from fastapi import Depends, HTTPException
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from api.services.quiz_service import QuizService
from api.services.answer_service import AnswerService
from config import DB_PATH, USE_LOCAL_STORAGE, FIPI_QUESTIONS_URL, is_stateless

def get_db_manager() -> DatabaseManager:
    return DatabaseManager(DB_PATH)

# --- Сервисы ---
def get_quiz_service(db: DatabaseManager = Depends(get_db_manager)) -> QuizService:
    return QuizService(db)

# --- Зависимости для сервисов ---
def get_storage() -> LocalStorage | None:
    if USE_LOCAL_STORAGE and not is_stateless(): # Не использовать storage в stateless режиме
        return LocalStorage("answers.json")
    return None

def get_answer_checker() -> FIPIAnswerChecker:
    return FIPIAnswerChecker(base_url=FIPI_QUESTIONS_URL)

def get_answer_service(
    db: DatabaseManager = Depends(get_db_manager),
    checker: FIPIAnswerChecker = Depends(get_answer_checker), # <-- Теперь get_answer_checker определён выше
    storage: LocalStorage | None = Depends(get_storage)
) -> AnswerService:
    return AnswerService(db, checker, storage)
