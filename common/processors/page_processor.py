"""
Module for processing scraped HTML pages into structured Problem objects.
This module provides the `PageProcessingOrchestrator` class which coordinates the parsing,
processing, and conversion of HTML pages into domain models.
"""
import asyncio
import logging
from typing import List, Tuple, Optional, Callable, Any
from pathlib import Path
from bs4 import BeautifulSoup, Tag

from common.models.problem_schema import Problem
from common.models.specification import SpecificationService
from common.utils.task_number_inferer import TaskNumberInferer
from processors.block_processor import BlockProcessor
from processors.asset_downloader import AssetDownloader

logger = logging.getLogger(__name__)


class PageProcessingOrchestrator:
    """
    Orchestrates the entire process of converting a scraped HTML page into Problem objects.
    
    It manages the flow from raw HTML parsing to final Problem model creation,
    coordinating various processors and converters.
    """

    def __init__(
        self,
        asset_downloader_factory: Callable[[Any, str, str], AssetDownloader],
        processors: Optional[List[Any]] = None,
        metadata_extractor: Optional[Any] = None,
        problem_builder: Optional[Any] = None,
        task_inferer: Optional[TaskNumberInferer] = None,
        specification_service: Optional[SpecificationService] = None, # Might be needed for TaskNumberInferer
    ):
        """
        Initializes the orchestrator with required dependencies.

        Args:
            asset_downloader_factory (Callable): A callable that returns an AssetDownloader instance.
                                                 Expected signature: (page, base_url, files_location_prefix) -> AssetDownloader.
            processors (List[Any], optional): List of HTML processors to apply. Not used directly here,
                                              as processors are instantiated internally for now.
                                              Reserved for future extensibility.
            metadata_extractor (Any, optional): Component for metadata extraction. Currently unused.
            problem_builder (Any, optional): Component for building Problem objects. Currently unused.
            task_inferer (TaskNumberInferer, optional): Component for inferring task numbers. Created internally if not provided.
            specification_service (SpecificationService, optional): Service for official specs. Needed to create TaskNumberInferer if not provided.
        """
        self.asset_downloader_factory = asset_downloader_factory
        self.processors = processors or []
        self.metadata_extractor = metadata_extractor
        self.problem_builder = problem_builder
        self.specification_service = specification_service
        
        # Initialize TaskNumberInferer if not provided
        if task_inferer is None:
            if specification_service is None:
                # Raise an error if neither inferer nor spec service is provided
                raise ValueError("Either 'task_inferer' or 'specification_service' must be provided to initialize PageProcessingOrchestrator.")
            self.task_inferer = TaskNumberInferer(spec_service=self.specification_service)
        else:
            self.task_inferer = task_inferer

        logger.debug("PageProcessingOrchestrator initialized.")

    async def process_page(
        self,
        page_content: str,
        base_url: str,
        files_location_prefix: str,
        page: Any,  # Playwright page object, passed to asset_downloader_factory
        subject: str,
        type: str,
        difficulty_level: str,
        exam_part: str,
        max_score: int,
    ) -> List[Problem]:
        """
        Processes a single HTML page into a list of Problem objects.

        Args:
            page_content: The raw HTML string of the page.
            base_url: The base URL of the site (e.g., https://ege.fipi.ru).
            files_location_prefix: A prefix for local file paths (e.g., 'data/raw/math/0/').
            page: The Playwright page object used for asset downloads.
            subject: The subject of the problems on this page.
            type: The type of problems (e.g., "A", "B", "task_1").
            difficulty_level: The difficulty level.
            exam_part: The exam part (e.g., "Part 1").
            max_score: The maximum score for problems on this page.

        Returns:
            A list of Problem objects extracted from the page.
        """
        logger.info(f"Processing page for subject '{subject}', type '{type}', part '{exam_part}'.")

        soup = BeautifulSoup(page_content, 'html.parser')

        # Create an instance of BlockProcessor
        block_processor = BlockProcessor(
            asset_downloader_factory=self.asset_downloader_factory,
            task_inferer=self.task_inferer,
            # Pass other necessary dependencies if required by BlockProcessor
        )

        # Process the soup using BlockProcessor
        # Assuming BlockProcessor.process_blocks returns List[Problem]
        problems = await block_processor.process_blocks(
            soup=soup,
            base_url=base_url,
            files_location_prefix=files_location_prefix,
            page=page,
            subject=subject,
            type=type,
            difficulty_level=difficulty_level,
            exam_part=exam_part,
            max_score=max_score,
        )

        logger.info(f"Successfully processed page into {len(problems)} Problem objects.")
        return problems

