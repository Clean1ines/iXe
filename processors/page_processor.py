"""
Module for orchestrating the processing of a single scraped HTML page into structured data.
This module provides the `PageProcessingOrchestrator` class which coordinates the parsing,
pairing, metadata extraction, asset downloading, and HTML transformation steps required
to convert raw FIPI page content into a list of `Problem` objects.
"""
import logging
from pathlib import Path
from typing import Any, Callable, List, Optional, Dict, Tuple
from bs4 import BeautifulSoup
from bs4.element import Tag
from utils.downloader import AssetDownloader
from utils.element_pairer import ElementPairer
from utils.metadata_extractor import MetadataExtractor
from models.problem_builder import ProblemBuilder
from processors.block_processor import BlockProcessor
from models.problem_schema import Problem
from domain.services.task_classifier import TaskClassificationService
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService
from services.specification import SpecificationService
from utils.task_number_inferer import TaskNumberInferer


logger = logging.getLogger(__name__)


class PageProcessingOrchestrator:
    """
    Orchestrates the processing of a complete HTML page into Problem objects.
    
    It handles the entire pipeline from raw HTML string to a list of structured Problems.
    """

    def __init__(
        self,
        task_inferer: TaskNumberInferer,
        specification_service: Optional[SpecificationService] = None,
    ):
        """
        Initializes the orchestrator with required services.

        Args:
            task_inferer: TaskNumberInferer for task classification logic
            specification_service: Optional SpecificationService for spec data
        """
        # Create domain services
        self.task_classifier = TaskClassificationService(task_inferer)
        self.answer_type_service = AnswerTypeService()
        self.metadata_enhancer = MetadataExtractionService(specification_service or SpecificationService(Path("data/specs/ege_2026_math_spec.json"), Path("data/specs/ege_2026_math_kes_kos.json")))
        
        # Create block processor with domain services
        self.block_processor = BlockProcessor(
            task_classifier=self.task_classifier,
            answer_type_service=self.answer_type_service,
            metadata_enhancer=self.metadata_enhancer,
            spec_service=specification_service
        )
        self.pairer = ElementPairer()

    async def process_page(
        self,
        page_content: str,
        subject: str,
        base_url: str,
        run_folder_page: Path,
        downloader: AssetDownloader,
        files_location_prefix: str = "",
    ) -> List[Problem]:
        """
        Processes the entire page content into a list of Problem objects.

        Args:
            page_content: The raw HTML string of the page.
            subject: The subject name (e.g., "math", "informatics").
            base_url: The base URL of the scraped page.
            run_folder_page: Path to the run folder for this page's assets.
            downloader: AssetDownloader instance for downloading files.
            files_location_prefix: Prefix for file paths in the output.

        Returns:
            A list of Problem objects extracted from the page.
        """
        logger.info(f"Starting to process page for subject '{subject}' with {len(page_content)} characters of content.")

        soup = BeautifulSoup(page_content, 'html.parser')
        paired_elements = self.pairer.pair(soup)

        problems = []
        for i, (header_container, qblock) in enumerate(paired_elements):
            problem = await self.block_processor.process_block(
                header_container=header_container,
                qblock=qblock,
                block_index=i,
                subject=subject,
                base_url=base_url,
                run_folder_page=run_folder_page,
                downloader=downloader,
                files_location_prefix=files_location_prefix,
            )
            problems.append(problem)

        logger.info(f"Completed processing page for subject '{subject}'. Generated {len(problems)} problems.")
        return problems
