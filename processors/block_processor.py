"""
Module for processing individual blocks of HTML content from FIPI pages.

This module provides the `BlockProcessor` class which encapsulates the logic
for processing a single block pair (header_container, qblock), including
applying HTML processors, downloading assets, extracting metadata, and
building Problem instances.
"""
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple
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
        building a Problem object.

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

        # Extract metadata first, before processors modify the header_container significantly
        metadata = self.metadata_extractor.extract(header_container)
        block_metadata = {
            "task_id": metadata["task_id"],
            "form_id": metadata["form_id"],
            "block_index": block_index
        }
        extracted_task_id = metadata["task_id"] or f"unknown_{block_index}"

        # Initialize and apply processors
        # Note: Processors list is expected to be passed during initialization
        # If not, we could instantiate them here as per the original logic
        # For now, we assume they are passed in self.processors
        # Or, if the list is empty, instantiate them as before:
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
                    if 'downloaded_images' in proc_metadata:
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

        # Build Problem instance
        problem_id = f"{page_num}_{extracted_task_id}"
        subject = "unknown_subject"  # TODO: pass subject or map proj_id
        type_str, difficulty_str = self._determine_task_type_and_difficulty(header_container)
        topics = self._extract_kes_codes(header_container)
        source_url = f"{base_url}?proj={proj_id}&page={page_num}"

        problem = self.problem_builder.build(
            problem_id=problem_id,
            subject=subject,
            type_str=type_str,
            text=assignment_text,
            topics=topics,
            difficulty=difficulty_str,
            source_url=source_url,
            metadata={"original_block_index": block_index, "proj_id": proj_id},
            processed_html_fragment=processed_html_string  # <-- NEW: pass processed HTML for offline use
        )

        logger.debug(f"Finished processing block {block_index}.")
        return processed_html_string, assignment_text, all_new_images, all_new_files, problem, block_metadata

    def _extract_kes_codes(self, header_container: Tag) -> List[str]:
        """Extracts KES codes from header container."""
        import re
        kes_codes = []
        kes_text = header_container.get_text(separator=' ', strip=True)
        kes_pattern = re.compile(r'\b[A-Z]?\d+(?:\.\d+)*\b')
        kes_codes = kes_pattern.findall(kes_text)
        return kes_codes

    def _determine_task_type_and_difficulty(self, header_container: Tag) -> Tuple[str, str]:
        """Determines task type and difficulty based on header text."""
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
