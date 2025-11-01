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
        """
        self.asset_downloader_factory = asset_downloader_factory
        self.processors = processors or []
        self.metadata_extractor = metadata_extractor
        self.problem_builder = problem_builder
        self.pairer = ElementPairer()
        self.metadata_extractor_instance = MetadataExtractor()
        self.problem_builder_instance = ProblemBuilder()

    async def process(
        self,
        page_content: str,
        proj_id: str,
        page_num: str,
        run_folder: Path,
        base_url: str,
        files_location_prefix: str = "../../",
        page: Any = None,
    ) -> List[Problem]:
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

        Returns:
            List[Problem]: A list of structured Problem objects extracted from the page.
        """
        soup = BeautifulSoup(page_content, 'html.parser')
        assets_dir = run_folder / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Initialize AssetDownloader using the factory
        asset_downloader = self.asset_downloader_factory(page, base_url, files_location_prefix)

        # --- Apply initial HTML processing steps ---
        # 1. Remove unwanted elements
        soup = UnwantedElementRemover().process(soup)
        # 2. Remove MathML
        soup = MathMLRemover().process(soup)
        # 3. Remove input fields (retained by default unless explicitly removed here)
        # soup = InputFieldRemover().process(soup) # Commented out as per user preference to retain input fields

        # --- Pair headers and qblocks ---
        paired_elements = self.pairer.pair(soup)
        logger.debug(f"Found {len(paired_elements)} header-qblock pairs on page {page_num}.")

        # --- Process each pair ---
        problems = []
        for i, (header_container, qblock) in enumerate(paired_elements):
            # Prepare processors for this block, injecting the asset_downloader
            image_processor = ImageScriptProcessor()
            file_processor = FileLinkProcessor()
            task_info_processor = TaskInfoProcessor()

            # Process assets within the qblock
            processed_qblock, image_metadata = image_processor.process(qblock, assets_dir, asset_downloader)
            processed_qblock, file_metadata = file_processor.process(processed_qblock, assets_dir, asset_downloader)
            processed_qblock, task_info_metadata = task_info_processor.process(processed_qblock) # TaskInfoProcessor doesn't download assets

            # Extract metadata from the header container
            header_metadata = self.metadata_extractor_instance.extract_from_header(header_container)

            # Combine metadata
            combined_metadata = {**header_metadata, **image_metadata, **file_metadata, **task_info_metadata}

            # Build Problem object
            problem = self.problem_builder_instance.build(
                header_container=header_container,
                qblock=processed_qblock,
                metadata=combined_metadata,
                proj_id=proj_id,
                page_num=page_num,
                run_folder=run_folder
            )
            if problem: # Check if problem was built successfully
                problems.append(problem)

        return problems

    # --- Удалены устаревшие методы: _extract_kes_codes, _determine_task_type_and_difficulty ---

