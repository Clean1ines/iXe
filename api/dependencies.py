from fastapi import Depends, Request
from qdrant_client import QdrantClient
from domain.interfaces.infrastructure_adapters import IDatabaseProvider
from infrastructure.adapters.local_storage_adapter import LocalStorageAdapterAdapter
from domain.interfaces.infrastructure_adapters import IExternalChecker
from services.quiz_service import QuizService
from services.answer_service import AnswerService
from utils.skill_graph import InMemorySkillGraph
from infrastructure.adapters.specification_adapter import SpecificationAdapter
from infrastructure.adapters.qdrant_retriever_adapter import QdrantRetrieverAdapter
from pathlib import Path
from config import DB_PATH, USE_LOCAL_STORAGE, FIPI_QUESTIONS_URL, QDRANT_HOST, QDRANT_PORT
from domain.exceptions.infrastructure import ExternalServiceException
from domain.exceptions.business import ResourceNotFoundException
from utils.logging_config import get_logger
from domain.services.observability_service import ObservabilityService
from infrastructure.adapters.database_adapter import DatabaseAdapter
from infrastructure.adapters.answer_checker_adapter import FIPIAnswerCheckerAdapterAdapter

logger = get_logger(__name__)

class Config:
    @staticmethod
    def is_stateless() -> bool:
        import os
        return os.getenv("STATELESS", "false").lower() == "true"


def get_db_manager() -> IDatabaseProvider:  # Изменено: теперь возвращает интерфейс
    """
    Dependency to provide an instance of DatabaseAdapter.

    Returns:
        DatabaseAdapter: An instance of the database manager.
    """
    return DatabaseAdapter(DB_PATH)


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
    db_manager: IDatabaseProvider = Depends(get_db_manager)  # Изменено: теперь принимает интерфейс
) -> QdrantRetrieverAdapter:
    """
    Dependency to provide an instance of QdrantRetrieverAdapter.

    Args:
        qdrant_client: The Qdrant client instance.
        db_manager: The database manager instance.

    Returns:
        QdrantRetrieverAdapter: An instance of the problem retriever.
    """
    try:
        return QdrantRetrieverAdapter(
            qdrant_client=qdrant_client,
            collection_name="problems",  # Укажите актуальное имя коллекции
            db_manager=db_manager
        )
    except Exception as e:
        raise ExternalServiceException(
            service_name="QdrantRetrieverAdapter",
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
    db: IDatabaseProvider = Depends(get_db_manager),  # Изменено: теперь принимает интерфейс
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
        return InMemorySkillGraph.build_from_db_and_specs(db, spec_service)  # Сохранено оригинальное поведение
    except Exception as e:
        raise ExternalServiceException(
            service_name="SkillGraphBuilder",
            message="Failed to build skill graph from database and specs",
            details={"error": str(e)}
        )


def get_storage() -> LocalStorageAdapterAdapter | None:
    """
    Dependency to provide an instance of LocalStorageAdapter or None.

    Returns:
        LocalStorageAdapter | None: An instance of local storage if enabled and not stateless, otherwise None.
    """
    if USE_LOCAL_STORAGE and not Config.is_stateless():
        return LocalStorageAdapterAdapter(Path("answers.json"))
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


async def get_answer_checker(browser_manager: object = Depends(get_browser_manager)) -> FIPIAnswerCheckerAdapterAdapter:
    """
    Dependency to provide an instance of FIPIAnswerCheckerAdapter.

    Args:
        browser_manager: The shared BrowserManager instance.

    Returns:
        FIPIAnswerCheckerAdapter: An instance of the answer checker.
    """
    # Note: The FIPIAnswerCheckerAdapter now expects a BrowserManager instance in its constructor.
    # This dependency function provides that instance.
    # The original 'base_url' argument is no longer used by FIPIAnswerCheckerAdapter.__init__.
    # We pass the browser_manager here.
    # The 'base_url' is now handled internally by BrowserManager or FIPIAnswerCheckerAdapter if needed for other purposes,
    # but the primary page acquisition is through BrowserManager.
    try:
        return FIPIAnswerCheckerAdapterAdapter(browser_manager=browser_manager)  # Исправлено: вызываем конкретный класс
    except Exception as e:
        raise ExternalServiceException(
            service_name="FIPIAnswerCheckerAdapter",
            message="Failed to initialize answer checker",
            details={"error": str(e)}
        )


def get_answer_service(
    db: IDatabaseProvider = Depends(get_db_manager),  # Изменено: теперь принимает интерфейс
    checker: FIPIAnswerCheckerAdapterAdapter = Depends(get_answer_checker),
    storage: LocalStorageAdapterAdapter | None = Depends(get_storage),
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
    db: IDatabaseProvider = Depends(get_db_manager),  # Изменено: теперь принимает интерфейс
    problem_retriever: QdrantRetrieverAdapter = Depends(get_problem_retriever),
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
