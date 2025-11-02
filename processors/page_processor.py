"""
Module for orchestrating the processing of a single scraped HTML page into structured data.
This module provides the `PageProcessingOrchestrator` class which coordinates the parsing,
pairing, metadata extraction, asset downloading, and HTML transformation steps required
to convert raw FIPI page content into a list of `Problem` objects.
"""
import logging
from pathlib import Path
from typing import Any, Callable, List, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag
from utils.downloader import AssetDownloader
from utils.element_pairer import ElementPairer
from utils.metadata_extractor import MetadataExtractor
from models.problem_builder import ProblemBuilder
from processors.html_data_processors import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover
)
from models.problem_schema import Problem
from processors.block_processor import BlockProcessor
from utils.task_number_inferer import TaskNumberInferer
from services.specification import SpecificationService

logger = logging.getLogger(__name__)


class PageProcessingOrchestrator:
    """
    Orchestrates the full processing pipeline for a single FIPI HTML page.
    
    This class coordinates the transformation of raw HTML content into structured
    `Problem` instances. It relies on injected dependencies (downloader factory, processors)
    to maintain modularity and testability.
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
        # self.pairer = ElementPairer() # Now handled by BlockProcessor or passed separately if needed in future
        # self.metadata_extractor_instance = MetadataExtractor() # Now handled by BlockProcessor
        # self.problem_builder_instance = ProblemBuilder() # Now handled by BlockProcessor
        self.task_inferer = task_inferer
        self.specification_service = specification_service
        # Create default instances if not provided
        if self.task_inferer is None and self.specification_service is not None:
            # Assume TaskNumberInferer can be created with spec_service
            # This might need adjustment based on TaskNumberInferer's actual init
            from utils.task_number_inferer import TaskNumberInferer
            self.task_inferer = TaskNumberInferer(spec_service=self.specification_service)

    async def process(
        self,
        page_content: str,
        proj_id: str,
        page_num: str,
        run_folder: Path,
        base_url: str,
        files_location_prefix: str = "../../",
        page: Any = None,
        subject: str = "unknown" # Need subject for BlockProcessor
    ) -> List[Problem]: # Return only the list of problems
        """
        Orchestrates the processing of a single HTML page content into Problems.

        Args:
            page_content (str): The raw HTML string of the page.
            proj_id (str): The project ID associated with the subject.
            page_num (str): The page number being processed.
            run_folder (Path): The base directory for this run's output.
            base_url (str): Base URL used to resolve relative asset paths.
            files_location_prefix (str): Prefix used for asset links in the processed HTML.
            page (Any, optional): Playwright page object, passed to AssetDownloader factory if needed.
            subject (str): The subject key (e.g., 'math') for inferring task numbers.

        Returns:
            List[Problem]: A list of structured Problem objects extracted from the page.
        """
        soup = BeautifulSoup(page_content, 'html.parser')
        assets_dir = run_folder / "assets"
        assets_dir.mkdir(exist_ok=True)

        # --- Pair headers and qblocks ---
        # This logic also might be internal to BlockProcessor, or we need ElementPairer here.
        # Let's assume PageProcessingOrchestrator still does pairing and BlockProcessor handles the rest.
        pairer = ElementPairer() # Create pairer instance for this process run
        paired_elements = pairer.pair(soup)
        logger.debug(f"Found {len(paired_elements)} header-qblock pairs on page {page_num}.")

        # --- Process each pair using BlockProcessor ---
        problems = []
        for i, (header_container, qblock) in enumerate(paired_elements):
            # Create BlockProcessor instance for this specific block
            # It needs the asset_downloader_factory, processors, metadata_extractor, problem_builder, task_inferer
            # OLD: image_processor = ImageScriptProcessor()
            # OLD: file_processor = FileLinkProcessor()
            # OLD: task_info_processor = TaskInfoProcessor()
            # OLD: processed_qblock, image_metadata = image_processor.process(qblock, assets_dir, downloader=asset_downloader)
            # OLD: processed_qblock, file_metadata = file_processor.process(processed_qblock, assets_dir, downloader=asset_downloader)
            # OLD: processed_qblock, task_info_metadata = task_info_processor.process(processed_qblock, assets_dir) # TaskInfoProcessor doesn't download assets
            # OLD: header_metadata = self.metadata_extractor_instance.extract_from_header(header_container)
            # OLD: combined_metadata = {**header_metadata, **image_metadata, **file_metadata, **task_info_metadata}
            # OLD: problem = self.problem_builder_instance.build(...)
            block_processor = BlockProcessor(
                asset_downloader_factory=self.asset_downloader_factory,
                processors=self.processors, # Pass the list of processors, BlockProcessor will instantiate them
                metadata_extractor=self.metadata_extractor or MetadataExtractor(),
                problem_builder=self.problem_builder or ProblemBuilder(),
                task_inferer=self.task_inferer # This must be provided or created
            )

            # Process the block and get the Problem object
            # OLD: ... (long manual processing)
            # NEW: Use BlockProcessor
            try:
                _, _, _, _, problem, _ = block_processor.process(
                    header_container=header_container,
                    qblock=qblock,
                    block_index=i,
                    page_num=page_num,
                    page_assets_dir=assets_dir, # Note: BlockProcessor expects page_assets_dir, which is run_folder / "assets"
                    proj_id=proj_id,
                    base_url=base_url,
                    subject=subject,
                    page=page,
                    files_location_prefix=files_location_prefix
                )
                if problem: # Check if problem was built successfully
                    problems.append(problem)
            except Exception as e:
                logger.error(f"Error processing block {i} (header id: {header_container.get('id')}, qblock id: {qblock.get('id')}): {e}", exc_info=True)
                # Decide whether to continue or raise
                # For now, continue to process other blocks
                continue

        return problems # Return only the list of problems

    # --- Удалены устаревшие методы: _extract_kes_codes, _determine_task_type_and_difficulty ---

