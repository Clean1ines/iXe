"""
Module for orchestrating the processing of a single scraped HTML page into structured data.
This module provides the `PageProcessingOrchestrator` class which coordinates the parsing,
pairing, metadata extraction, asset downloading, and HTML transformation steps required
to convert raw FIPI page content into a list of `Problem` objects and legacy scraped data.
It delegates the processing of individual blocks to the `BlockProcessor`.
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
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

logger = logging.getLogger(__name__)


class PageProcessingOrchestrator:
    """
    Orchestrates the full processing pipeline for a single FIPI HTML page.

    This class coordinates the transformation of raw HTML content into structured
    `Problem` instances and a legacy-compatible scraped data dictionary. It relies
    on injected dependencies (downloader factory, processors) and delegates the
    processing of individual blocks to the `BlockProcessor` to maintain modularity
    and testability.
    """

    def __init__(
        self,
        asset_downloader_factory: Callable[[Any, str, str], AssetDownloader],
        processors: Optional[List[Any]] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
        problem_builder: Optional[ProblemBuilder] = None,
        block_processor: Optional[BlockProcessor] = None,
        element_pairer: Optional[ElementPairer] = None,
    ):
        """
        Initializes the orchestrator with required dependencies.

        Args:
            asset_downloader_factory (Callable): A callable that returns an AssetDownloader instance.
                                                 Expected signature: (page, base_url, files_location_prefix) -> AssetDownloader.
            processors (List[Any], optional): List of HTML processors to apply. If not provided,
                                              a default set will be instantiated.
            metadata_extractor (MetadataExtractor, optional): Component for metadata extraction.
            problem_builder (ProblemBuilder, optional): Component for building Problem objects.
            block_processor (BlockProcessor, optional): Instance of BlockProcessor. If not provided,
                                                       one will be created using other dependencies.
            element_pairer (ElementPairer, optional): Instance of ElementPairer. If not provided,
                                                     one will be created.
        """
        self.asset_downloader_factory = asset_downloader_factory
        # Use provided processors or instantiate default ones
        self.processors = processors or [
            ImageScriptProcessor(),
            FileLinkProcessor(),
            TaskInfoProcessor(),
            InputFieldRemover(),
            MathMLRemover(),
            UnwantedElementRemover()
        ]
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.problem_builder = problem_builder or ProblemBuilder()

        if block_processor is None:
            # Create a default BlockProcessor instance using the provided or default dependencies
            self.block_processor = BlockProcessor(
                asset_downloader_factory=self.asset_downloader_factory,
                processors=self.processors,
                metadata_extractor=self.metadata_extractor,
                problem_builder=self.problem_builder
            )
        else:
            self.block_processor = block_processor

        # Inject ElementPairer dependency
        self.pairer = element_pairer or ElementPairer()

    def process(
        self,
        page_content: str,
        proj_id: str,
        page_num: str,
        run_folder: Path,
        base_url: str,
        files_location_prefix: str = "../../",
        page: Any = None,
    ) -> Tuple[List[Problem], Dict[str, Any]]:
        """
        Orchestrates the processing of a single HTML page content into Problems and scraped data.

        This method pairs headers and qblocks, iterates through them, and delegates
        the processing of each block pair to the `BlockProcessor`. It then aggregates
        the results into the final output structures.

        Args:
            page_content (str): The raw HTML string of the page.
            proj_id (str): The project ID associated with the subject.
            page_num (str): The page number being processed.
            run_folder (Path): The base directory for this run's output.
            base_url (str): Base URL used to resolve relative asset paths.
            files_location_prefix (str): Prefix used by FIPI for asset paths (e.g., '../../').
            page (Any): Playwright page object used for asset downloading (required by AssetDownloader).

        Returns:
            Tuple[List[Problem], Dict[str, Any]]: A tuple containing:
                - A list of `Problem` objects created from the page content.
                - A dictionary with the old scraped data structure (page_name, blocks_html, etc.).
        """
        logger.info(f"Starting processing of page {page_num} for project {proj_id}")
        page_soup = BeautifulSoup(page_content, "html.parser")

        # Use the injected ElementPairer
        paired_elements = self.pairer.pair(page_soup)
        logger.info(f"Found and paired {len(paired_elements)} header-qblock sets on page {page_num}.")

        # Prepare output directories and accumulators
        page_assets_dir = run_folder / page_num / "assets"
        page_assets_dir.mkdir(parents=True, exist_ok=True)

        problems: List[Problem] = []
        processed_blocks_html: List[str] = []
        assignments_text: List[str] = []
        downloaded_images: Dict[str, str] = {}
        downloaded_files: Dict[str, str] = {}
        task_metadata: List[Dict[str, Any]] = []

        # Process each block pair using BlockProcessor
        for idx, (header_container, qblock) in enumerate(paired_elements):
            try:
                # --- DELEGATE TO BLOCK PROCESSOR ---
                logger.debug(f"Delegating processing of block pair {idx} to BlockProcessor...")
                processed_html, assignment_text, new_images, new_files, problem, block_metadata = self.block_processor.process(
                    header_container=header_container,
                    qblock=qblock,
                    block_index=idx,
                    page_num=page_num,
                    page_assets_dir=page_assets_dir,
                    proj_id=proj_id,
                    base_url=base_url,
                    page=page,
                    files_location_prefix=files_location_prefix
                )
                # --- COLLECT RESULTS ---
                processed_blocks_html.append(processed_html)
                assignments_text.append(assignment_text)
                downloaded_images.update(new_images)
                downloaded_files.update(new_files)
                problems.append(problem)
                task_metadata.append(block_metadata)
                # -------------------------------
                logger.info(f"Block pair {idx} processed successfully by BlockProcessor.")
            except Exception as e:
                logger.error(f"Error processing block pair {idx} with BlockProcessor: {e}", exc_info=True)
                # Optional: Add a placeholder Problem or skip the block
                # For now, we skip the block and continue.
                continue

        scraped_data = {
            "page_name": page_num,
            "url": f"{base_url}?proj={proj_id}&page={page_num}",
            "assignments": assignments_text,
            "blocks_html": processed_blocks_html,
            "images": downloaded_images,
            "files": downloaded_files,
            "task_metadata": task_metadata
        }

        logger.info(f"Successfully processed {len(processed_blocks_html)} blocks for page {page_num}.")
        return problems, scraped_data

    def _extract_kes_codes(self, header_container: Tag) -> List[str]:
        """Extracts KES codes from header container."""
        kes_codes = []
        kes_text = header_container.get_text(separator=' ', strip=True)
        kes_pattern = re.compile(r'\b[A-Z]?\d+(?:\.\d+)*\b')
        kes_codes = kes_pattern.findall(kes_text)
        return kes_codes

    def _determine_task_type_and_difficulty(self, header_container: Tag) -> Tuple[str, str]:
        """Determines task type and difficulty based on header text."""
        type_str = "unknown"
        difficulty_str = "unknown"
        header_text = header_container.get_text(separator=' ', strip=True)
        match = re.search(r'(?:Задание\s+)?([A-Z]?\d+)', header_text)
        if match:
            task_num = match.group(1)
            if task_num.startswith('A'):
                type_str = "multiple_choice"
                difficulty_str = "easy"
            elif task_num.startswith('B'):
                type_str = "short_answer"
                difficulty_str = "medium"
            elif task_num.startswith('C'):
                type_str = "extended_answer"
                difficulty_str = "hard"
            else:
                num = int(task_num) if task_num.isdigit() else 0
                if 1 <= num <= 12:
                    type_str = f"task_{num}"
                    difficulty_str = "easy" if num <= 5 else "medium"
                elif 13 <= num <= 20:
                    type_str = f"task_{num}"
                    difficulty_str = "hard"
                else:
                    type_str = f"task_{num}"
                    difficulty_str = "medium"
        return type_str, difficulty_str
