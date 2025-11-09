"""
Infrastructure adapter for processing individual blocks of HTML content from FIPI pages.

This module provides the `BlockProcessorAdapter` class which implements the domain
interface IHTMLProcessor and encapsulates the logic for processing a single block
pair (header_container, qblock), including applying HTML processors, downloading
assets, extracting metadata, and building Problem instances with correct task_number
inferred from KES codes.
"""
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import Tag
import asyncio
from datetime import datetime

from utils.downloader import AssetDownloader
from processors.html import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover
)
from infrastructure.adapters.html_metadata_extractor_adapter import HTMLMetadataExtractorAdapter
from domain.models.problem_builder import ProblemBuilder
from domain.models.problem_schema import Problem
from domain.interfaces.html_processor import IHTMLProcessor
from domain.interfaces.task_inferer import ITaskNumberInferer
from domain.interfaces.html_processor import ITaskClassifier
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService
from infrastructure.adapters.specification_adapter import SpecificationAdapter
from domain.interfaces.html_processor import IHTMLProcessor as IHTMLProcessorImpl


logger = logging.getLogger(__name__)


class BlockProcessorAdapter(IHTMLProcessor):
    """
    Infrastructure adapter implementing domain interface for processing a single problem block from FIPI pages.
    
    It takes paired header and question blocks, applies a series of transformations
    (asset downloading, HTML cleaning), extracts metadata, and builds a Problem instance.
    """

    def __init__(
        self,
        task_inferer: ITaskNumberInferer,
        task_classifier: ITaskClassifier,
        answer_type_service: AnswerTypeService,
        metadata_enhancer: MetadataExtractionService,
        spec_service: Optional[SpecificationAdapter] = None,
    ):
        """
        Initializes the BlockProcessorAdapter with required services.

        Args:
            task_inferer: Domain interface for inferring task numbers
            task_classifier: Domain interface for classifying tasks
            answer_type_service: Service for detecting answer types
            metadata_enhancer: Service for enhancing metadata with spec data
            spec_service: Optional specification service (needed for metadata enhancer)
        """
        self.task_inferer = task_inferer
        self.task_classifier = task_classifier
        self.answer_type_service = answer_type_service
        self.metadata_enhancer = metadata_enhancer
        self.spec_service = spec_service

    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str,
        base_url: str,
        run_folder_page: Path,
        downloader: AssetDownloader,
        files_location_prefix: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Processes a single block pair (header_container, qblock) into structured data.

        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics").
            base_url: The base URL of the scraped page.
            run_folder_page: Path to the run folder for this page's assets.
            downloader: AssetDownloader instance for downloading files.
            files_location_prefix: Prefix for file paths in the output.
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary containing structured data from the processed block.
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
        metadata_extractor = HTMLMetadataExtractorAdapter()
        metadata = metadata_extractor.extract_metadata_from_header(header_container)
        kes_codes = metadata.get('kes_codes', [])
        kos_codes = metadata.get('kos_codes', [])
        assignment_text = combined_soup.get_text(separator='\n', strip=True)

        # --- 3. Detect answer type ---
        html_content_str = str(combined_soup)
        answer_type = self.answer_type_service.detect_answer_type(html_content_str)

        # --- 4. Classify the task using domain interface ---
        classification_result = self.task_classifier.classify_task(kes_codes, kos_codes, answer_type)
        task_number = classification_result.get('task_number', 0) or 0
        difficulty_level = classification_result.get('difficulty_level', 'basic')
        max_score = classification_result.get('max_score', 1)

        # --- 5. Apply HTML processors ---
        processors: List[IHTMLProcessorImpl] = [
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

        # --- 7. Return structured data with all required Problem fields ---
        result = {
            'problem_id': f"{subject}_{block_index}_{hash(processed_html_string) % 1000000}",
            'subject': subject,
            'type': f"task_{task_number}" if task_number > 0 else "unknown",
            'text': processed_html_string,
            'answer': None,  # Answers are not scraped from the question itself
            'options': None,
            'solutions': None,
            'kes_codes': kes_codes,
            'skills': None,
            'difficulty_level': difficulty_level,
            'task_number': task_number,
            'kos_codes': kos_codes,
            'exam_part': "Part 1" if task_number <= 12 else "Part 2",
            'max_score': max_score,
            'form_id': None,
            'source_url': base_url,
            'raw_html_path': None,
            'created_at': datetime.now(),
            'updated_at': None,
            'metadata': enhanced_metadata,
            # These are aliases, not direct fields in Problem
            # 'assignment_text': assignment_text,
            # 'topics': kes_codes,
            # 'requirements': kos_codes,
        }

        logger.debug(f"Finished processing block {block_index} with task_number={task_number}.")
        return result

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
        Extracts KOS codes reliably by parsing the structured 'КЭС:' line.

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
