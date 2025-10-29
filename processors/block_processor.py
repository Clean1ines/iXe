"""
Module for processing individual blocks of HTML content from FIPI pages.

This module provides the `BlockProcessor` class which encapsulates the logic
for processing a single block pair (header_container, qblock), including
applying HTML processors, downloading assets, extracting metadata, and
building Problem instances with extended metadata fields.
"""
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag

from utils.downloader import AssetDownloader
from processors.html_data_processors import (
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


logger = logging.getLogger(__name__)


class BlockProcessor:
    """
    A class responsible for processing a single block of HTML content.

    This processor handles the transformation of a block pair (header_container, qblock)
    into processed HTML, extracted text, downloaded assets, and a structured Problem object.
    It coordinates the use of various asset processors, metadata extraction, and problem building.
    """

    def __init__(
        self,
        asset_downloader_factory: Callable[[Any, str, str], AssetDownloader],
        processors: List[Any],
        metadata_extractor: MetadataExtractor,
        problem_builder: ProblemBuilder,
    ):
        """
        Initializes the BlockProcessor with required dependencies.

        Args:
            asset_downloader_factory (Callable): A callable that returns an AssetDownloader instance.
                                                 Expected signature: (page, base_url, files_location_prefix) -> AssetDownloader.
            processors (List[Any]): List of HTML processors to apply. Expected to be instances of AssetProcessor.
            metadata_extractor (MetadataExtractor): Component for extracting metadata from header containers.
            problem_builder (ProblemBuilder): Component for building Problem objects.
        """
        self.asset_downloader_factory = asset_downloader_factory
        self.processors = processors
        self.metadata_extractor = metadata_extractor
        self.problem_builder = problem_builder
        self._spec_cache: Optional[Dict] = None

    def _load_specification(self) -> Dict:
        """
        Loads the exam specification from file or returns a default mapping.
        
        Returns:
            Dict: A mapping of task numbers to their metadata (exam_part, max_score, difficulty_level).
        """
        if self._spec_cache is not None:
            return self._spec_cache
            
        spec_path = Path("data/specs/ege_2026_math_spec.json")
        default_spec = self._get_default_spec()
        
        if spec_path.exists():
            try:
                with open(spec_path, 'r', encoding='utf-8') as f:
                    spec = json.load(f)
                    self._spec_cache = spec
                    return spec
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Failed to load spec file {spec_path}, using default spec: {e}")
        
        self._spec_cache = default_spec
        return default_spec

    def _get_default_spec(self) -> Dict:
        """
        Returns a default exam specification mapping task numbers to metadata.
        
        Returns:
            Dict: Default mapping for exam specifications.
        """
        # Default mapping based on typical ЕГЭ structure
        spec = {}
        
        # Part 1: Tasks 1-12, typically max_score 1, difficulty easy-medium
        for i in range(1, 13):
            spec[str(i)] = {
                "exam_part": "part1",
                "max_score": 1,
                "difficulty_level": "easy" if i <= 6 else "medium"
            }
        
        # Part 2: Tasks 13-15, typically max_score 2, difficulty medium
        for i in range(13, 16):
            spec[str(i)] = {
                "exam_part": "part2",
                "max_score": 2,
                "difficulty_level": "medium"
            }
        
        # Part 2: Tasks 16-17, typically max_score 3, difficulty hard
        for i in range(16, 18):
            spec[str(i)] = {
                "exam_part": "part2",
                "max_score": 3,
                "difficulty_level": "hard"
            }
        
        # Part 2: Tasks 18-19, typically max_score 4, difficulty hard
        for i in range(18, 20):
            spec[str(i)] = {
                "exam_part": "part2",
                "max_score": 4,
                "difficulty_level": "hard"
            }
        
        return spec

    def process(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        page_num: str,
        page_assets_dir: Path,
        proj_id: str,
        base_url: str,
        page: Any = None,
        files_location_prefix: str = "../../"
    ) -> Tuple[str, str, Dict[str, str], Dict[str, str], Problem, Dict[str, Any]]:
        """
        Processes a single block pair (header_container, qblock).

        This involves applying various HTML processors, downloading assets,
        removing unwanted elements, extracting final HTML and text, and
        building a Problem object with extended metadata fields.

        Args:
            header_container (Tag): The BeautifulSoup Tag for the header container.
            qblock (Tag): The BeautifulSoup Tag for the qblock.
            block_index (int): The index of this block on the page.
            page_num (str): The current page number being processed.
            page_assets_dir (Path): The directory to save downloaded assets for this page.
            proj_id (str): The project ID associated with the subject.
            base_url (str): Base URL used to resolve relative asset paths.
            page (Any): Playwright page object used for asset downloading (required by AssetDownloader).
            files_location_prefix (str): Prefix used by FIPI for asset paths (e.g., '../../').

        Returns:
            Tuple[str, str, Dict[str, str], Dict[str, str], Problem, Dict[str, Any]]: A tuple containing:
                - processed_html_string (str): The final HTML string for the processed block.
                - assignment_text (str): The plain text extracted from the processed block.
                - new_images_dict (Dict[str, str]): A map of original image URLs to local paths.
                - new_files_dict (Dict[str, str]): A map of original file URLs to local paths.
                - problem (Problem): The constructed Problem instance for this block.
                - block_metadata (Dict[str, Any]): Metadata for this block, including task_id, form_id, and block_index.
        """
        logger.debug(f"Processing block {block_index}...")
        combined_soup = BeautifulSoup('', 'html.parser')
        combined_soup.append(qblock.extract())

        # Get downloader instance
        downloader = self.asset_downloader_factory(page, base_url, files_location_prefix)

        # Extract metadata from header_container
        metadata = self.metadata_extractor.extract(header_container)
        # Extract form_id from qblock
        qblock_id = qblock.get('id', '') # Извлекаем id из qblock
        logger.debug(f"Extracted qblock_id (used as form_id): '{qblock_id}' for block {block_index}")

        block_metadata = {
            "task_id": metadata["task_id"],
            "form_id": qblock_id, # Используем id qblock как form_id
            "block_index": block_index
        }
        extracted_task_id = metadata["task_id"] or f"unknown_{block_index}"

        # Initialize and apply processors
        if not self.processors:
            image_proc = ImageScriptProcessor()
            file_proc = FileLinkProcessor()
            info_proc = TaskInfoProcessor()
            input_remover = InputFieldRemover()
            math_remover = MathMLRemover()
            unwanted_remover = UnwantedElementRemover()
            processors_to_apply = [image_proc, file_proc, info_proc, input_remover, math_remover, unwanted_remover]
        else:
            processors_to_apply = self.processors

        # Accumulate metadata from processors
        all_new_images = {}
        all_new_files = {}

        # Process images inside <a> tags (previews for downloads)
        for a_tag in combined_soup.find_all('a'):
            img_tag = a_tag.find('img')
            if img_tag:
                img_src = img_tag.get('src')
                if img_src:
                    clean_img_src = img_src.lstrip('../../')
                    local_img_path = downloader.download(clean_img_src, page_assets_dir / "assets", asset_type='image')
                    if local_img_path:
                        img_relative_path_from_html = local_img_path.relative_to(page_assets_dir)
                        img_tag['src'] = str(img_relative_path_from_html)
                        logger.debug(f"Updated img src inside <a> to local file: {img_tag['src']}")
                    else:
                        logger.warning(f"Failed to download image {clean_img_src} for assignment pair {block_index} on page {page_num}.")

        # Apply processors that return (soup, metadata)
        for processor in processors_to_apply:
            if hasattr(processor, 'process') and callable(processor.process):
                # Check if processor needs downloader
                if hasattr(processor, '__class__') and processor.__class__.__name__ in ['ImageScriptProcessor', 'FileLinkProcessor']:
                    processed_soup, proc_metadata = processor.process(combined_soup, page_assets_dir.parent, downloader=downloader)
                else:
                    processed_soup, proc_metadata = processor.process(combined_soup, page_assets_dir.parent)

                combined_soup = processed_soup
                # Accumulate metadata from processors
                if isinstance(proc_metadata, dict):
                    if 'downloaded_images' in proc_metadata: # Исправлено: было 'proc_meta'
                        all_new_images.update(proc_metadata['downloaded_images'])
                    if 'downloaded_files' in proc_metadata:
                        all_new_files.update(proc_metadata['downloaded_files'])

        # Remove duplicate or undefined <img> tags
        for img_tag in combined_soup.find_all('img'):
            if img_tag.get('alt') == 'undefined' or img_tag.get('align') or img_tag.get('border'):
                img_tag.decompose()

        # Append task-header-panel after qblock
        task_header_panel = header_container.find('div', class_='task-header-panel')
        if task_header_panel:
            info_button = task_header_panel.find('div', class_='info-button')
            if info_button:
                header_soup_temp = BeautifulSoup('', 'html.parser')
                header_soup_temp.append(task_header_panel)
                # Find the specific TaskInfoProcessor instance
                info_proc = next((p for p in processors_to_apply if isinstance(p, TaskInfoProcessor)), TaskInfoProcessor())
                processed_header_soup, _ = info_proc.process(header_soup_temp, page_assets_dir.parent)
                header_soup_temp = processed_header_soup
                task_header_panel = header_soup_temp.find('div', class_='task-header-panel')
                logger.debug(f"Processed task-info for assignment pair {block_index}.")
            combined_soup.append(task_header_panel.extract())
            logger.debug(f"Appended task-header-panel for assignment pair {block_index}.")
        else:
            logger.warning(f"No task-header-panel found in header container for assignment pair {block_index}")

        # Remove all remaining scripts
        for script_tag in combined_soup.find_all('script'):
            script_tag.decompose()

        processed_html_string = str(combined_soup)
        assignment_text = combined_soup.get_text(separator='\n', strip=True)

        # Extract new fields
        task_number = self._extract_task_number(header_container, metadata)
        kes_codes = self._extract_kes_codes(header_container)
        kos_codes = self._extract_kos_codes(header_container)
        
        # Determine additional metadata from spec
        spec_data = self._load_specification()
        spec_entry = spec_data.get(str(task_number), {})
        exam_part = spec_entry.get("exam_part", "unknown")
        max_score = spec_entry.get("max_score", 1)
        difficulty_level = spec_entry.get("difficulty_level", "medium")  # Use spec difficulty, fallback to medium
        
        # Determine type based on header (fallback if not in spec)
        type_str, header_difficulty = self._determine_task_type_and_difficulty(header_container)
        # Use spec difficulty if available, otherwise fallback to header detection
        if difficulty_level == "medium" and header_difficulty != "unknown":
            difficulty_level = header_difficulty

        # Build Problem instance - Fixed: Define problem_id before using it
        problem_id = f"{page_num}_{extracted_task_id}"
        source_url = f"{base_url}?proj={proj_id}&page={page_num}"
        logger.debug(f"form_id for problem {problem_id} (from qblock id): '{qblock_id}'")
        problem = self.problem_builder.build(
            problem_id=problem_id,
            subject="math",  # TODO: pass subject or map proj_id
            type_str=type_str,
            text=assignment_text,
            topics=kes_codes,
            difficulty=difficulty_level,  # Pass as difficulty_level
            source_url=source_url,
            form_id=qblock_id, # Передаём id qblock как form_id
            meta={"original_block_index": block_index, "proj_id": proj_id}, # Fixed: use 'meta' instead of 'metadata'
            task_number=task_number,
            kes_codes=kes_codes,
            kos_codes=kos_codes,
            exam_part=exam_part,
            max_score=max_score,
            difficulty_level=difficulty_level
        )

        logger.debug(f"Finished processing block {block_index}.")
        return processed_html_string, assignment_text, all_new_images, all_new_files, problem, block_metadata

    def _extract_task_number(self, header_container: Tag, metadata: Dict[str, Any]) -> int: # Fixed: argument name from 'meta' to 'metadata'
        """
        Extracts the task number from the header container.
        
        Args:
            header_container (Tag): The BeautifulSoup Tag for the header container.
            metadata (Dict[str, Any]): Metadata extracted by MetadataExtractor.
            
        Returns:
            int: The task number, or 0 if not found.
        """
        import re
        # First try to get from metadata
        task_id = metadata.get("task_id") # Fixed: use 'metadata' instead of undefined 'meta'
        if task_id and task_id.isdigit():
            return int(task_id)
        
        # Then try to extract from header text
        header_text = header_container.get_text(separator=' ', strip=True)
        # Look for patterns like "Задание N" or just a number that seems to be the task number
        match = re.search(r'Задание\s+([A-Z]?\d+)', header_text)
        if match:
            task_num = match.group(1)
            # Extract just the numeric part if it's like A1, B2, etc.
            num_match = re.search(r'\d+', task_num)
            if num_match:
                return int(num_match.group(0))
        
        # Try to find a number that looks like a task number
        matches = re.findall(r'\b([A-Z]?\d+)\b', header_text)
        for match in matches:
            num_match = re.search(r'\d+', match)
            if num_match:
                return int(num_match.group(0))
        
        return 0

    def _extract_kos_codes(self, header_container: Tag) -> List[str]:
        """
        Extracts KOS codes from header container.
        
        Args:
            header_container (Tag): The BeautifulSoup Tag for the header container.
            
        Returns:
            List[str]: List of KOS codes found in the header.
        """
        import re
        kos_codes = []
        kos_text = header_container.get_text(separator=' ', strip=True)
        # Look for patterns like "КОС: 1.2.3" or "Коды: 1.2.3, 4.5.6"
        kos_pattern = re.compile(r'КОС[:\s]*([A-Z]?\d+(?:\.\d+)*)', re.IGNORECASE)
        kos_matches = kos_pattern.findall(kos_text)
        kos_codes.extend(kos_matches)
        
        # Also look for "Коды" pattern
        codes_pattern = re.compile(r'Коды[:\s]*([A-Z]?\d+(?:\.\d+)*(?:[,;\s]+[A-Z]?\d+(?:\.\d+)*)*)', re.IGNORECASE)
        codes_match = codes_pattern.search(kos_text)
        individual_codes = [] # Fixed: Initialize individual_codes here to avoid NameError if codes_match is None
        if codes_match:
            codes_str = codes_match.group(1)
            # Split by comma or semicolon and extract individual codes
            individual_codes = re.findall(r'[A-Z]?\d+(?:\.\d+)*', codes_str)
        kos_codes.extend(individual_codes) # Fixed: individual_codes is now always defined before this line
        
        return list(set(kos_codes))  # Remove duplicates

    def _extract_kes_codes(self, header_container: Tag) -> List[str]:
        """
        Extracts KES codes from header container.
        
        Args:
            header_container (Tag): The BeautifulSoup Tag for the header container.
            
        Returns:
            List[str]: List of KES codes found in the header.
        """
        import re
        kes_codes = []
        kes_text = header_container.get_text(separator=' ', strip=True)
        kes_pattern = re.compile(r'\b[A-Z]?\d+(?:\.\d+)*\b')
        kes_codes = kes_pattern.findall(kes_text)
        return kes_codes

    def _determine_task_type_and_difficulty(self, header_container: Tag) -> Tuple[str, str]:
        """
        Determines task type and difficulty based on header text.
        
        Args:
            header_container (Tag): The BeautifulSoup Tag for the header container.
            
        Returns:
            Tuple[str, str]: A tuple containing type and difficulty strings.
        """
        import re
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

