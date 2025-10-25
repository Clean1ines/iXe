"""
Module for orchestrating the processing of a single scraped HTML page into structured data.
This module provides the `PageProcessingOrchestrator` class which coordinates the parsing,
pairing, metadata extraction, asset downloading, and HTML transformation steps required
to convert raw FIPI page content into a list of `Problem` objects and legacy scraped data.
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
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
from models.problem_schema import Problem

logger = logging.getLogger(__name__)


class PageProcessingOrchestrator:
    """
    Orchestrates the full processing pipeline for a single FIPI HTML page.
    
    This class coordinates the transformation of raw HTML content into structured
    `Problem` instances and a legacy-compatible scraped data dictionary. It relies
    on injected dependencies (downloader factory, processors) to maintain modularity
    and testability.
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

        # Pair header containers with qblocks
        paired_elements = self._pair_elements(page_soup)
        logger.info(f"Found and paired {len(paired_elements)} header-qblock sets on page {page_num}.")

        # Initialize downloader
        downloader = self.asset_downloader_factory(page, base_url, files_location_prefix)

        # Prepare output directories and accumulators
        page_assets_dir = run_folder / page_num / "assets"
        page_assets_dir.mkdir(parents=True, exist_ok=True)

        problems: List[Problem] = []
        processed_blocks_html: List[str] = []
        assignments_text: List[str] = []
        downloaded_images: Dict[str, str] = {}
        downloaded_files: Dict[str, str] = {}
        task_metadata: List[Dict[str, Any]] = []

        # Process each block pair
        for idx, (header_container, qblock) in enumerate(paired_elements):
            # Extract metadata
            metadata = self._extract_metadata_for_block(header_container)
            task_metadata.append({
                "task_id": metadata["task_id"],
                "form_id": metadata["form_id"],
                "block_index": idx
            })

            # Process the block
            processed_html, assignment_text, new_images, new_files = self._process_single_block(
                header_container, qblock, idx, page_num, page_assets_dir, downloader
            )
            processed_blocks_html.append(processed_html)
            assignments_text.append(assignment_text)
            downloaded_images.update(new_images)
            downloaded_files.update(new_files)

            # Build Problem object (stubbed logic copied from FIPIScraper)
            extracted_task_id = metadata["task_id"] or f"unknown_{idx}"
            problem_id = f"{page_num}_{extracted_task_id}"
            subject = "unknown_subject"  # TODO: pass subject or map proj_id
            type_str, difficulty_str = self._determine_task_type_and_difficulty(header_container)
            topics = self._extract_kes_codes(header_container)

            problem = Problem(
                problem_id=problem_id,
                subject=subject,
                type=type_str,
                text=assignment_text,
                options=None,
                answer="placeholder_answer",
                solutions=None,
                topics=topics,
                skills=None,
                difficulty=difficulty_str,
                source_url=f"{base_url}?proj={proj_id}&page={page_num}",
                raw_html_path=None,
                created_at=datetime.now(),
                updated_at=None,
                metadata={"original_block_index": idx, "proj_id": proj_id}
            )
            problems.append(problem)

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

    def _pair_elements(self, page_soup: BeautifulSoup) -> List[Tuple[Tag, Tag]]:
        """
        Finds and pairs 'qblock' divs with their preceding/following 'header container' divs.

        Args:
            page_soup (BeautifulSoup): The parsed BeautifulSoup object of the page.

        Returns:
            List[Tuple[Tag, Tag]]: A list of tuples, where each tuple contains
                                (header_container_tag, qblock_tag).
        """
        logger.debug("Starting element pairing process.")
        qblocks = page_soup.find_all('div', class_='qblock')
        header_containers = page_soup.find_all('div', id=re.compile(r'^i'))
        logger.debug(f"Found {len(qblocks)} qblocks and {len(header_containers)} header containers for pairing.")

        body_children = page_soup.body.children if page_soup.body else []
        ordered_elements = []
        current_qblock_idx = 0
        current_header_idx = 0

        for child in body_children:
            if child.name == 'div':
                if child.get('class') and 'qblock' in child.get('class'):
                    if current_qblock_idx < len(qblocks):
                        ordered_elements.append(('qblock', qblocks[current_qblock_idx]))
                        current_qblock_idx += 1
                elif child.get('id') and child.get('id', '').startswith('i'):
                    if current_header_idx < len(header_containers):
                        ordered_elements.append(('header', header_containers[current_header_idx]))
                        current_header_idx += 1

        paired_elements = []
        i = 0
        while i < len(ordered_elements):
            if ordered_elements[i][0] == 'header' and i + 1 < len(ordered_elements) and ordered_elements[i + 1][0] == 'qblock':
                header_soup = ordered_elements[i][1]
                qblock_soup = ordered_elements[i + 1][1]
                paired_elements.append((header_soup, qblock_soup))
                i += 2
            elif ordered_elements[i][0] == 'qblock' and i + 1 < len(ordered_elements) and ordered_elements[i + 1][0] == 'header':
                qblock_soup = ordered_elements[i][1]
                header_soup = ordered_elements[i + 1][1]
                paired_elements.append((header_soup, qblock_soup))
                i += 2
            else:
                logger.warning(f"Unpaired element found at index {i}: {ordered_elements[i][0]}")
                i += 1

        logger.info(f"Successfully paired {len(paired_elements)} header-qblock sets.")
        return paired_elements

    def _extract_metadata_for_block(self, header_container: Tag) -> Dict[str, str]:
        """
        Extracts task-specific metadata (task_id, form_id) from a header container.

        Args:
            header_container (Tag): The BeautifulSoup Tag representing the header container.

        Returns:
            Dict[str, str]: A dictionary containing 'task_id' and 'form_id'.
                            Values are empty strings if not found.
        """
        task_id = ""
        form_id = ""
        # Extract task_id
        canselect_span = header_container.find('span', class_='canselect')
        if canselect_span:
            task_id = canselect_span.get_text(strip=True)
        logger.debug(f"Extracted task_id: '{task_id}'")
        # Extract form_id
        answer_button = header_container.find('span', class_='answer-button')
        if answer_button and answer_button.get('onclick'):
            onclick = answer_button['onclick']
            form_match = re.search(r"checkButtonClick\(\s*['\"]([^'\"]+)['\"]", onclick)
            if form_match:
                form_id = form_match.group(1)
                logger.debug(f"Extracted form_id: '{form_id}'")
        return {"task_id": task_id, "form_id": form_id}

    def _process_single_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        page_num: str,
        page_assets_dir: Path,
        downloader: AssetDownloader
    ) -> Tuple[str, str, Dict[str, str], Dict[str, str]]:
        """
        Processes a single pair of (header_container, qblock) elements.

        This involves applying various HTML processors, downloading assets,
        removing unwanted elements, and extracting final HTML and text.

        Args:
            header_container (Tag): The BeautifulSoup Tag for the header container.
            qblock (Tag): The BeautifulSoup Tag for the qblock.
            block_index (int): The index of this block on the page.
            page_num (str): The current page number being processed.
            page_assets_dir (Path): The directory to save downloaded assets for this page.
            downloader (AssetDownloader): The downloader instance to use for assets.

        Returns:
            Tuple[str, str, Dict[str, str], Dict[str, str]]: A tuple containing:
                - processed_html_string (str): The final HTML string for the processed block.
                - assignment_text (str): The plain text extracted from the processed block.
                - new_images_dict (Dict[str, str]): A map of original image URLs to local paths.
                - new_files_dict (Dict[str, str]): A map of original file URLs to local paths.
        """
        logger.debug(f"Processing block {block_index}...")
        combined_soup = BeautifulSoup('', 'html.parser')
        combined_soup.append(qblock.extract())

        # Process images inside <a> tags (previews for downloads)
        for a_tag in combined_soup.find_all('a'):
            img_tag = a_tag.find('img')
            if img_tag:
                img_src = img_tag.get('src')
                if img_src:
                    clean_img_src = img_src.lstrip('../../')
                    local_img_path = downloader.download(clean_img_src, page_assets_dir, asset_type='image')
                    if local_img_path:
                        img_relative_path_from_html = local_img_path.relative_to(page_assets_dir.parent)
                        img_tag['src'] = str(img_relative_path_from_html)
                        logger.debug(f"Updated img src inside <a> to local file: {img_tag['src']}")
                    else:
                        logger.warning(f"Failed to download image {clean_img_src} for assignment pair {block_index} on page {page_num}.")

        # Initialize and apply processors
        image_proc = ImageScriptProcessor(downloader)
        file_proc = FileLinkProcessor(downloader)
        info_proc = TaskInfoProcessor()
        input_remover = InputFieldRemover()
        math_remover = MathMLRemover()
        unwanted_remover = UnwantedElementRemover()

        combined_soup, new_imgs = image_proc.process(combined_soup, page_assets_dir.parent)
        combined_soup, new_files = file_proc.process(combined_soup, page_assets_dir.parent)
        combined_soup = input_remover.process(combined_soup)
        combined_soup = math_remover.process(combined_soup)

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
                header_soup_temp = info_proc.process(header_soup_temp)
                task_header_panel = header_soup_temp.find('div', class_='task-header-panel')
                logger.debug(f"Processed task-info for assignment pair {block_index}.")
            combined_soup.append(task_header_panel.extract())
            logger.debug(f"Appended task-header-panel for assignment pair {block_index}.")
        else:
            logger.warning(f"No task-header-panel found in header container for assignment pair {block_index}")

        # Apply UnwantedElementRemover AFTER extracting task_id/form_id
        combined_soup = unwanted_remover.process(combined_soup)

        # Remove all remaining scripts
        for script_tag in combined_soup.find_all('script'):
            script_tag.decompose()

        processed_html_string = str(combined_soup)
        assignment_text = combined_soup.get_text(separator='\n', strip=True)
        logger.debug(f"Finished processing block {block_index}.")
        return processed_html_string, assignment_text, new_imgs, new_files

    def _extract_task_id(self, header_container: Tag) -> str:
        """Extracts task_id from header container (kept for compatibility)."""
        task_id = ""
        canselect_span = header_container.find('span', class_='canselect')
        if canselect_span:
            task_id = canselect_span.get_text(strip=True)
        return task_id

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
