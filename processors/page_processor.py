"""
Module for orchestrating the processing of a single scraped HTML page into structured data.
This module provides the `PageProcessingOrchestrator` class which coordinates the parsing,
pairing, metadata extraction, asset downloading, and HTML transformation steps required
to convert raw FIPI page content into a list of structured data dictionaries.
"""
import logging
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup
from utils.downloader import AssetDownloader
from utils.element_pairer import ElementPairer
from infrastructure.adapters.block_processor_adapter import BlockProcessorAdapter
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService
from services.specification import SpecificationService
from infrastructure.adapters.task_classifier_adapter import TaskClassifierAdapter
from infrastructure.adapters.task_number_inferer_adapter import TaskNumberInfererAdapter


logger = logging.getLogger(__name__)


class PageProcessingOrchestrator:
    """
    Orchestrates the processing of a complete HTML page into structured data.
    
    It handles the entire pipeline from raw HTML string to a list of structured data dictionaries.
    """

    def __init__(
        self,
        task_classifier_adapter: TaskClassifierAdapter,
        task_inferer_adapter: TaskNumberInfererAdapter,
        answer_type_service: Optional[AnswerTypeService] = None,
        metadata_enhancer: Optional[MetadataExtractionService] = None,
        specification_service: Optional[SpecificationService] = None,
    ):
        """
        Initializes the orchestrator with required services.

        Args:
            task_classifier_adapter: TaskClassifierAdapter for task classification logic
            task_inferer_adapter: TaskNumberInfererAdapter for task number inference
            answer_type_service: AnswerTypeService for answer type detection
            metadata_enhancer: MetadataExtractionService for metadata enhancement
            specification_service: Optional SpecificationService for spec data
        """
        self.task_classifier_adapter = task_classifier_adapter
        self.task_inferer_adapter = task_inferer_adapter
        self.answer_type_service = answer_type_service or AnswerTypeService()
        self.metadata_enhancer = metadata_enhancer or MetadataExtractionService(
            specification_service or SpecificationService(
                Path("data/specs/ege_2026_math_spec.json"), 
                Path("data/specs/ege_2026_math_kes_kos.json")
            )
        )
        
        # Create block processor with domain services
        self.block_processor = BlockProcessorAdapter(
            task_inferer=self.task_inferer_adapter,
            task_classifier=self.task_classifier_adapter,
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
    ) -> List[dict]:
        """
        Processes the entire page content into a list of structured data dictionaries.

        Args:
            page_content: The raw HTML string of the page.
            subject: The subject name (e.g., "math", "informatics").
            base_url: The base URL of the scraped page.
            run_folder_page: Path to the run folder for this page's assets.
            downloader: AssetDownloader instance for downloading files.
            files_location_prefix: Prefix for file paths in the output.

        Returns:
            A list of structured data dictionaries extracted from the page.
        """
        logger.info(f"Starting to process page for subject '{subject}' with {len(page_content)} characters of content.")

        soup = BeautifulSoup(page_content, 'html.parser')
        paired_elements = self.pairer.pair(soup)

        results = []
        for i, (header_container, qblock) in enumerate(paired_elements):
            result = await self.block_processor.process_html_block(
                header_container=header_container,
                qblock=qblock,
                block_index=i,
                subject=subject,
                base_url=base_url,
                run_folder_page=run_folder_page,
                downloader=downloader,
                files_location_prefix=files_location_prefix,
            )
            results.append(result)

        logger.info(f"Completed processing page for subject '{subject}'. Generated {len(results)} results.")
        return results
