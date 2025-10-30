from fastapi import Depends
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from config import DB_PATH, USE_LOCAL_STORAGE, FIPI_QUESTIONS_URL

def get_db_manager() -> DatabaseManager:
    return DatabaseManager(DB_PATH)

def get_storage() -> LocalStorage | None:
    if USE_LOCAL_STORAGE:
        return LocalStorage("answers.json")
    return None

def get_answer_checker() -> FIPIAnswerChecker:
    return FIPIAnswerChecker(base_url=FIPI_QUESTIONS_URL)
