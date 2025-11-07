"""
Module for processing individual blocks of HTML content from FIPI pages.

This module provides the `BlockProcessor` class which encapsulates the logic
for processing a single block pair (header_container, qblock), including
applying HTML processors, downloading assets, extracting metadata, and
building Problem instances with correct task_number inferred from KES codes.
"""
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import Tag
import asyncio

from utils.downloader import AssetDownloader
from processors.html import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover
)
from utils.metadata_extractor import MetadataExtractor
from models.problem_builder import ProblemBuilder
from models.problem_schema import Problem
from domain.services.task_classifier import TaskClassificationService
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService
from services.specification import SpecificationService
from processors.html_processor_interface import IHTMLProcessor


logger = logging.getLogger(__name__)


class BlockProcessor:
    """
    A class responsible for processing a single problem block from FIPI pages.
    
    It takes paired header and question blocks, applies a series of transformations
    (asset downloading, HTML cleaning), extracts metadata, and builds a Problem instance.
    """

    def __init__(
        self,
        task_classifier: TaskClassificationService,
        answer_type_service: AnswerTypeService,
        metadata_enhancer: MetadataExtractionService,
        spec_service: Optional[SpecificationService] = None,
    ):
        """
        Initializes the BlockProcessor with required services.

        Args:
            task_classifier: Service for classifying tasks based on KES/KOS codes
            answer_type_service: Service for detecting answer types
            metadata_enhancer: Service for enhancing metadata with spec data
            spec_service: Optional specification service (needed for metadata enhancer)
        """
        self.task_classifier = task_classifier
        self.answer_type_service = answer_type_service
        self.metadata_enhancer = metadata_enhancer
        self.spec_service = spec_service

    async def process_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str,
        base_url: str,
        run_folder_page: Path,
        downloader: AssetDownloader,
        files_location_prefix: str = "",
    ) -> Problem:
        """
        Processes a single block pair (header_container, qblock) into a Problem instance.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics").
            base_url: The base URL of the scraped page.
            run_folder_page: Path to the run folder for this page's assets.
            downloader: AssetDownloader instance for downloading files.
            files_location_prefix: Prefix for file paths in the output.

        Returns:
            A Problem instance built from the processed block.
        """
        logger.debug(f"Starting processing of block {block_index} for subject '{subject}'.")

        # --- 1. Combine header and question blocks ---
        combined_soup = BeautifulSoup('', 'html.parser')
        combined_soup.append(qblock.extract())
        
        # Extract and process the header separately
        task_header_panel = header_container.find('div', class_='task-header-panel')
        if task_header_panel:
            # Process header-specific elements (info buttons, etc.)
            info_proc = TaskInfoProcessor()
            header_soup_temp = BeautifulSoup('', 'html.parser')
            header_soup_temp.append(task_header_panel)
            # Convert to string and process with IHTMLProcessor
            header_content_str = str(header_soup_temp)
            processed_header_content, _ = await info_proc.process(header_content_str, {'run_folder_page': run_folder_page})
            processed_header_soup = BeautifulSoup(processed_header_content, 'html.parser')
            task_header_panel = processed_header_soup.find('div', class_='task-header-panel')
            combined_soup.append(task_header_panel.extract())

        # --- 2. Extract metadata (KES, KOS codes) ---
        metadata_extractor = MetadataExtractor()
        metadata = metadata_extractor.extract_metadata_from_header(header_container)
        kes_codes = metadata.get('kes_codes', [])
        kos_codes = metadata.get('kos_codes', [])
        assignment_text = combined_soup.get_text(separator='\n', strip=True)

        # --- 3. Detect answer type ---
        html_content_str = str(combined_soup)
        answer_type = self.answer_type_service.detect_answer_type(html_content_str)

        # --- 4. Classify the task using domain service ---
        classification_result = self.task_classifier.classify_task(kes_codes, kos_codes, answer_type)
        task_number = classification_result.task_number or 0
        difficulty_level = classification_result.difficulty_level
        max_score = classification_result.max_score

        # --- 5. Apply HTML processors ---
        processors: List[IHTMLProcessor] = [
            MathMLRemover(),
            UnwantedElementRemover(),
            FileLinkProcessor(),
            ImageScriptProcessor(),
            InputFieldRemover(),
        ]

        processed_html_string = str(combined_soup)
        all_proc_metadata = {}
        
        for processor in processors:
            # Process with IHTMLProcessor interface
            processed_html_string, proc_metadata = await processor.process(
                processed_html_string, 
                {
                    'run_folder_page': run_folder_page,
                    'downloader': downloader,
                    'base_url': base_url,
                    'files_location_prefix': files_location_prefix
                }
            )
            all_proc_metadata.update(proc_metadata)

        # --- 6. Enhance metadata using domain service ---
        enhanced_metadata = self.metadata_enhancer.enhance_metadata(metadata)

        # --- 7. Build the Problem instance ---
        problem_builder = ProblemBuilder()
        problem = problem_builder.build_problem(
            problem_id=f"{subject}_{block_index}_{hash(processed_html_string) % 1000000}",
            subject=subject,
            type=f"task_{task_number}" if task_number > 0 else "unknown",
            text=processed_html_string,
            answer=None,  # Answers are not scraped from the question itself
            options=None,
            assignment_text=assignment_text,
            kes_codes=kes_codes,
            kos_codes=kos_codes,
            task_number=task_number,
            exam_part="Part 1" if task_number <= 12 else "Part 2",
            difficulty=difficulty_level,
            max_score=max_score,
            topics=kes_codes,  # topics is an alias for kes_codes
            requirements=kos_codes,  # requirements is an alias for kos_codes
        )

        logger.debug(f"Finished processing block {block_index} with task_number={task_number}.")
        return problem

    def _extract_kes_codes_reliable(self, header_container: Tag) -> List[str]:
        """
        Extracts KES codes reliably by parsing the structured 'КЭС:' line.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.

        Returns:
            List of extracted KES codes.
        """
        # This method is now primarily for internal use or fallback
        # The main extraction should happen in MetadataExtractor
        kes_codes = []
        # Find elements that contain the text "КЭС"
        for element in header_container.find_all(string=re.compile(r"КЭС|кодификатор", re.IGNORECASE)):
            parent = element.parent
            # Look for patterns like "КЭС: 1.1, 1.2" or "Кодификатор: 2.1.1"
            text = parent.get_text()
            # Improved regex to capture codes more accurately
            kes_pattern = r'(?:КЭС|кодификатор):\s*([0-9.,\s-]+)'
            matches = re.findall(kes_pattern, text, re.IGNORECASE)
            for match in matches:
                # Split by comma and clean up individual codes
                codes = [code.strip() for code in match.split(',')]
                kes_codes.extend(codes)
        
        # Remove duplicates while preserving order
        kes_codes = list(dict.fromkeys(kes_codes))
        return kes_codes

    def _extract_kos_codes_reliable(self, header_container: Tag) -> List[str]:
        """
        Extracts KOS codes reliably by parsing the structured 'КОС:' line.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.

        Returns:
            List of extracted KOS codes.
        """
        # This method is now primarily for internal use or fallback
        # The main extraction should happen in MetadataExtractor
        kos_codes = []
        # Find elements that contain the text "КОС"
        for element in header_container.find_all(string=re.compile(r"КОС|требование", re.IGNORECASE)):
            parent = element.parent
            # Look for patterns like "КОС: 1, 2" or "Требование: 3.1"
            text = parent.get_text()
            # Improved regex to capture codes more accurately
            kos_pattern = r'(?:КОС|требование):\s*([0-9.,\s-]+)'
            matches = re.findall(kos_pattern, text, re.IGNORECASE)
            for match in matches:
                # Split by comma and clean up individual codes
                codes = [code.strip() for code in match.split(',')]
                kos_codes.extend(codes)
        
        # Remove duplicates while preserving order
        kos_codes = list(dict.fromkeys(kos_codes))
        return kos_codes
