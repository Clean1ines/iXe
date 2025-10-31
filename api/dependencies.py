from fastapi import Depends, HTTPException
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from api.services.quiz_service import QuizService
from api.services.answer_service import AnswerService
from utils.skill_graph import InMemorySkillGraph
from services.specification import SpecificationService
from pathlib import Path
from config import DB_PATH, USE_LOCAL_STORAGE, FIPI_QUESTIONS_URL, is_stateless

def get_db_manager() -> DatabaseManager:
    """
    Dependency to provide an instance of DatabaseManager.

    Returns:
        DatabaseManager: An instance of the database manager.
    """
    return DatabaseManager(DB_PATH)

def get_spec_service() -> SpecificationService:
    """
    Dependency to provide an instance of SpecificationService.

    Returns:
        SpecificationService: An instance of the specification service.
    """
    SPEC_DIR = Path(__file__).parent.parent / "data" / "specs"
    return SpecificationService(
        spec_path=SPEC_DIR / "ege_2026_math_spec.json",
        kes_kos_path=SPEC_DIR / "ege_2026_math_kes_kos.json"
    )

def get_skill_graph(
    db: DatabaseManager = Depends(get_db_manager),
    spec_service: SpecificationService = Depends(get_spec_service)
) -> InMemorySkillGraph:
    """
    Dependency to provide an instance of InMemorySkillGraph.

    Args:
        db: The database manager instance.
        spec_service: The specification service instance.

    Returns:
        InMemorySkillGraph: An instance of the in-memory skill graph.
    """
    return InMemorySkillGraph.build_from_db_and_specs(db, spec_service)

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
    storage: LocalStorage | None = Depends(get_storage),
    skill_graph: InMemorySkillGraph = Depends(get_skill_graph)
) -> AnswerService:
    """
    Dependency to provide an instance of AnswerService.

    Args:
        db: The database manager instance.
        checker: The answer checker instance.
        storage: Optional local storage instance.
        skill_graph: The in-memory skill graph instance.

    Returns:
        AnswerService: An instance of the answer service.
    """
    return AnswerService(db, checker, storage, skill_graph)
