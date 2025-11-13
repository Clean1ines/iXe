"""
Dependency injection container for the application.

This container manages the creation and lifecycle of all application
dependencies, ensuring proper wiring of components according to
clean architecture principles.
"""
import logging
from typing import Dict, Any
from domain.interfaces.external_services import (
    IBrowserService,
    IDatabaseService,
    ISpecificationService
)
from infrastructure.adapters.browser_service_adapter import BrowserServiceAdapter
from infrastructure.adapters.database_service_adapter import DatabaseServiceAdapter
from infrastructure.adapters.specification_adapter import SpecificationAdapter
from application.services.page_scraping_service import PageScrapingService
from application.services.scraping_service import ScrapingService
from application.factories.problem_factory import ProblemFactory
from application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from infrastructure.adapters.html_element_pairer_adapter import HTMLElementPairerAdapter
from infrastructure.adapters.fipi_html_metadata_extractor import FIPIHTMLMetadataExtractor
from infrastructure.adapters.task_classifier_adapter import TaskClassifierAdapter
from infrastructure.adapters.task_number_inferer_adapter import TaskNumberInfererAdapter
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService
from infrastructure.adapters.block_processor_adapter import BlockProcessorAdapter

logger = logging.getLogger(__name__)

class ApplicationContainer:
    """
    Application dependency container.
    
    Business Rules:
    - Creates and manages all application dependencies
    - Ensures proper dependency injection
    - Handles resource cleanup
    - Supports different environments (dev, prod, test)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize container with configuration.
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self._instances = {}
    
    def get_scrape_subject_use_case(self) -> ScrapeSubjectUseCase:
        """Get scrape subject use case."""
        if 'scrape_subject_use_case' not in self._instances:
            self._instances['scrape_subject_use_case'] = self._create_scrape_subject_use_case()
        return self._instances['scrape_subject_use_case']
    
    def _create_scrape_subject_use_case(self) -> ScrapeSubjectUseCase:
        """Create scrape subject use case with dependencies."""
        return ScrapeSubjectUseCase(
            browser_service=self.get_browser_service(),
            database_service=self.get_database_service(),
            specification_service=self.get_specification_service(),
            page_scraping_service=self.get_page_scraping_service(),
            problem_factory=self.get_problem_factory()
        )
    
    def get_browser_service(self) -> IBrowserService:
        """Get browser service instance."""
        if 'browser_service' not in self._instances:
            self._instances['browser_service'] = BrowserServiceAdapter(
                max_browsers=self.config.get('browser_pool_size', 3),
                headless=self.config.get('browser_headless', True),
                timeout_seconds=self.config.get('browser_timeout', 30),
                user_agent=self.config.get('user_agent')
            )
        return self._instances['browser_service']
    
    def get_database_service(self) -> IDatabaseService:
        """Get database service instance."""
        if 'database_service' not in self._instances:
            db_path = self.config.get('database_path', 'data/fipi_data.db')
            self._instances['database_service'] = DatabaseServiceAdapter(db_path)
        return self._instances['database_service']
    
    def get_specification_service(self) -> ISpecificationService:
        """Get specification service instance."""
        if 'specification_service' not in self._instances:
            spec_path = self.config.get('spec_path', 'data/specs/ege_2026_math_spec.json')
            kes_kos_path = self.config.get('kes_kos_path', 'data/specs/ege_2026_math_kes_kos.json')
            self._instances['specification_service'] = SpecificationAdapter(
                spec_path=spec_path,
                kes_kos_path=kes_kos_path
            )
        return self._instances['specification_service']
    
    def get_page_scraping_service(self) -> PageScrapingService:
        """Get page scraping service instance."""
        if 'page_scraping_service' not in self._instances:
            self._instances['page_scraping_service'] = PageScrapingService(
                browser_service=self.get_browser_service(),
                database_service=self.get_database_service(),
                block_processor=self.get_block_processor_adapter(),
                problem_factory=self.get_problem_factory()
            )
        return self._instances['page_scraping_service']
    
    def get_block_processor_adapter(self) -> BlockProcessorAdapter:
        """Get block processor adapter instance."""
        if 'block_processor_adapter' not in self._instances:
            self._instances['block_processor_adapter'] = BlockProcessorAdapter(
                task_inferer=self.get_task_number_inferer_adapter(),
                task_classifier=self.get_task_classifier_adapter(),
                answer_type_service=self.get_answer_type_service(),
                metadata_enhancer=self.get_metadata_enhancer(),
                spec_service=self.get_specification_service()
            )
        return self._instances['block_processor_adapter']
    
    def get_task_number_inferer_adapter(self) -> TaskNumberInfererAdapter:
        """Get task number inferer adapter instance."""
        if 'task_number_inferer_adapter' not in self._instances:
            self._instances['task_number_inferer_adapter'] = TaskNumberInfererAdapter(
                spec_service=self.get_specification_service()
            )
        return self._instances['task_number_inferer_adapter']
    
    def get_task_classifier_adapter(self) -> TaskClassifierAdapter:
        """Get task classifier adapter instance."""
        if 'task_classifier_adapter' not in self._instances:
            self._instances['task_classifier_adapter'] = TaskClassifierAdapter(
                inferer=self.get_task_number_inferer_adapter()
            )
        return self._instances['task_classifier_adapter']
    
    def get_answer_type_service(self) -> AnswerTypeService:
        """Get answer type service instance."""
        if 'answer_type_service' not in self._instances:
            self._instances['answer_type_service'] = AnswerTypeService()
        return self._instances['answer_type_service']
    
    def get_metadata_enhancer(self) -> MetadataExtractionService:
        """Get metadata enhancer service instance."""
        if 'metadata_enhancer' not in self._instances:
            self._instances['metadata_enhancer'] = MetadataExtractionService(
                spec_service=self.get_specification_service()
            )
        return self._instances['metadata_enhancer']
    
    def get_problem_factory(self) -> ProblemFactory:
        """Get problem factory instance."""
        if 'problem_factory' not in self._instances:
            self._instances['problem_factory'] = ProblemFactory()
        return self._instances['problem_factory']
    
    async def shutdown(self) -> None:
        """Clean up all resources."""
        logger.info("Shutting down application container...")
        
        # Clean up browser service
        if 'browser_service' in self._instances:
            browser_service = self._instances['browser_service']
            await browser_service.close()
        
        self._instances.clear()
        logger.info("Application container shutdown complete")
