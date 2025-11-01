from fastapi import Depends
from qdrant_client import QdrantClient
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from api.services.quiz_service import QuizService
from api.services.answer_service import AnswerService
from utils.skill_graph import InMemorySkillGraph
from services.specification import SpecificationService
from utils.retriever import QdrantProblemRetriever
from pathlib import Path
from config import DB_PATH, USE_LOCAL_STORAGE, FIPI_QUESTIONS_URL, QDRANT_HOST, QDRANT_PORT


class Config:
    @staticmethod
    def is_stateless() -> bool:
        import os
        return os.getenv("STATELESS", "false").lower() == "true"


def get_db_manager() -> DatabaseManager:
    """
    Dependency to provide an instance of DatabaseManager.

    Returns:
        DatabaseManager: An instance of the database manager.
    """
    return DatabaseManager(DB_PATH)


def get_qdrant_client() -> QdrantClient:
    """
    Dependency to provide an instance of QdrantClient.

    Returns:
        QdrantClient: An instance of the Qdrant client.
    """
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_problem_retriever(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    db_manager: DatabaseManager = Depends(get_db_manager)
) -> QdrantProblemRetriever:
    """
    Dependency to provide an instance of QdrantProblemRetriever.

    Args:
        qdrant_client: The Qdrant client instance.
        db_manager: The database manager instance.

    Returns:
        QdrantProblemRetriever: An instance of the problem retriever.
    """
    return QdrantProblemRetriever(
        qdrant_client=qdrant_client,
        collection_name="problems",  # Укажите актуальное имя коллекции
        db_manager=db_manager
    )


def get_spec_service(subject: str, year: str) -> SpecificationService:
    """
    Dependency to provide an instance of SpecificationService.

    Args:
        subject: The subject name (e.g., 'math', 'informatics').
        year: The year for the specifications (e.g., '2026').

    Returns:
        SpecificationService: An instance of the specification service.
    """
    SPEC_DIR = Path(__file__).parent.parent / "data" / "specs"
    return SpecificationService(
        spec_path=SPEC_DIR / f"ege_{year}_{subject}_spec.json",
        kes_kos_path=SPEC_DIR / f"ege_{year}_{subject}_kes_kos.json"
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


def get_storage() -> LocalStorage | None:
    """
    Dependency to provide an instance of LocalStorage or None.

    Returns:
        LocalStorage | None: An instance of local storage if enabled and not stateless, otherwise None.
    """
    if USE_LOCAL_STORAGE and not Config.is_stateless():
        return LocalStorage(Path("answers.json"))
    return None


def get_answer_checker() -> FIPIAnswerChecker:
    """
    Dependency to provide an instance of FIPIAnswerChecker.

    Returns:
        FIPIAnswerChecker: An instance of the answer checker.
    """
    return FIPIAnswerChecker(base_url=FIPI_QUESTIONS_URL)


def get_quiz_service(
    problem_retriever: QdrantProblemRetriever = Depends(get_problem_retriever)
) -> QuizService:
    """
    Dependency to provide an instance of QuizService.

    Args:
        problem_retriever: The problem retriever instance.

    Returns:
        QuizService: An instance of the quiz service.
    """
    return QuizService(problem_retriever)


def get_answer_service(
    db: DatabaseManager = Depends(get_db_manager),
    checker: FIPIAnswerChecker = Depends(get_answer_checker),
    storage: LocalStorage | None = Depends(get_storage),
    skill_graph: InMemorySkillGraph = Depends(get_skill_graph),
    spec_service: SpecificationService = Depends(get_spec_service)
) -> AnswerService:
    """
    Dependency to provide an instance of AnswerService.

    Args:
        db: The database manager instance.
        checker: The answer checker instance.
        storage: Optional local storage instance.
        skill_graph: The in-memory skill graph instance.
        spec_service: The specification service instance.

    Returns:
        AnswerService: An instance of the answer service.
    """
    return AnswerService(db, checker, storage, skill_graph, spec_service)
