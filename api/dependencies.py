from fastapi import Depends, Request
from qdrant_client import QdrantClient
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from services.quiz_service import QuizService
from services.answer_service import AnswerService
from utils.skill_graph import InMemorySkillGraph
from infrastructure.adapters.specification_adapter import SpecificationAdapter
from utils.retriever import QdrantProblemRetriever
from pathlib import Path
from config import DB_PATH, USE_LOCAL_STORAGE, FIPI_QUESTIONS_URL, QDRANT_HOST, QDRANT_PORT
from domain.exceptions.infrastructure import ExternalServiceException
from domain.exceptions.business import ResourceNotFoundException
from utils.logging_config import get_logger
from domain.services.observability_service import ObservabilityService

logger = get_logger(__name__)

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
    try:
        return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    except Exception as e:
        raise ExternalServiceException(
            service_name="Qdrant",
            message=f"Failed to connect to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}",
            details={"error": str(e)}
        )


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
    try:
        return QdrantProblemRetriever(
            qdrant_client=qdrant_client,
            collection_name="problems",  # Укажите актуальное имя коллекции
            db_manager=db_manager
        )
    except Exception as e:
        raise ExternalServiceException(
            service_name="QdrantProblemRetriever",
            message="Failed to initialize problem retriever",
            details={"error": str(e)}
        )


def get_spec_service(subject: str, year: str) -> SpecificationAdapter:
    """
    Dependency to provide an instance of SpecificationAdapter.

    Args:
        subject: The subject name (e.g., 'math', 'informatics').
        year: The year for the specifications (e.g., '2026').

    Returns:
        SpecificationAdapter: An instance of the specification service.
    """
    SPEC_DIR = Path(__file__).parent.parent / "data" / "specs"
    spec_path = SPEC_DIR / f"ege_{year}_{subject}_spec.json"
    kes_kos_path = SPEC_DIR / f"ege_{year}_{subject}_kes_kos.json"
    
    if not spec_path.exists():
        raise ResourceNotFoundException(
            resource_type="Specification",
            resource_id=f"{year}_{subject}",
            details={"spec_path": str(spec_path)}
        )
    
    return SpecificationAdapter(
        spec_path=spec_path,
        kes_kos_path=kes_kos_path
    )


def get_skill_graph(
    db: DatabaseManager = Depends(get_db_manager),
    spec_service: SpecificationAdapter = Depends(get_spec_service)
) -> InMemorySkillGraph:
    """
    Dependency to provide an instance of InMemorySkillGraph.

    Args:
        db: The database manager instance.
        spec_service: The specification service instance.

    Returns:
        InMemorySkillGraph: An instance of the in-memory skill graph.
    """
    try:
        return InMemorySkillGraph.build_from_db_and_specs(db, spec_service)
    except Exception as e:
        raise ExternalServiceException(
            service_name="SkillGraphBuilder",
            message="Failed to build skill graph from database and specs",
            details={"error": str(e)}
        )


def get_storage() -> LocalStorage | None:
    """
    Dependency to provide an instance of LocalStorage or None.

    Returns:
        LocalStorage | None: An instance of local storage if enabled and not stateless, otherwise None.
    """
    if USE_LOCAL_STORAGE and not Config.is_stateless():
        return LocalStorage(Path("answers.json"))
    return None


def get_browser_manager(request: Request):
    """
    Dependency to provide the shared BrowserManager instance.

    Args:
        request: The incoming request object.

    Returns:
        BrowserManager: The shared instance managed by the app's lifespan.
    """
    return request.app.state.browser_manager


async def get_answer_checker(browser_manager: object = Depends(get_browser_manager)) -> FIPIAnswerChecker:
    """
    Dependency to provide an instance of FIPIAnswerChecker.

    Args:
        browser_manager: The shared BrowserManager instance.

    Returns:
        FIPIAnswerChecker: An instance of the answer checker.
    """
    # Note: The FIPIAnswerChecker now expects a BrowserManager instance in its constructor.
    # This dependency function provides that instance.
    # The original 'base_url' argument is no longer used by FIPIAnswerChecker.__init__.
    # We pass the browser_manager here.
    # The 'base_url' is now handled internally by BrowserManager or FIPIAnswerChecker if needed for other purposes,
    # but the primary page acquisition is through BrowserManager.
    try:
        return FIPIAnswerChecker(browser_manager=browser_manager)
    except Exception as e:
        raise ExternalServiceException(
            service_name="FIPIAnswerChecker",
            message="Failed to initialize answer checker",
            details={"error": str(e)}
        )


def get_answer_service(
    db: DatabaseManager = Depends(get_db_manager),
    checker: FIPIAnswerChecker = Depends(get_answer_checker),
    storage: LocalStorage | None = Depends(get_storage),
    skill_graph: InMemorySkillGraph = Depends(get_skill_graph),
    spec_service: SpecificationAdapter = Depends(get_spec_service)
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
    try:
        return AnswerService(db, checker, storage, skill_graph, spec_service)
    except Exception as e:
        raise ExternalServiceException(
            service_name="AnswerService",
            message="Failed to initialize answer service",
            details={"error": str(e)}
        )


def get_quiz_service(
    db: DatabaseManager = Depends(get_db_manager),
    problem_retriever: QdrantProblemRetriever = Depends(get_problem_retriever),
    skill_graph: InMemorySkillGraph = Depends(get_skill_graph),
    spec_service: SpecificationAdapter = Depends(get_spec_service)
) -> QuizService:
    """
    Dependency to provide an instance of QuizService.

    Args:
        db: The database manager instance.
        problem_retriever: The problem retriever instance.
        skill_graph: The in-memory skill graph instance.
        spec_service: The specification service instance.

    Returns:
        QuizService: An instance of the quiz service.
    """
    try:
        return QuizService(db, problem_retriever, skill_graph, spec_service)
    except Exception as e:
        raise ExternalServiceException(
            service_name="QuizService",
            message="Failed to initialize quiz service",
            details={"error": str(e)}
        )


def get_browser_pool_manager(request: Request):
    """
    Dependency to provide the shared BrowserPoolManager instance.

    Args:
        request: The incoming request object.

    Returns:
        BrowserPoolManager: The shared instance managed by the app's lifespan.
    """
    return request.app.state.browser_pool_manager
