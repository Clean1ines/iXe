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
from utils.task_number_inferer import TaskNumberInferer


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
        task_inferer: TaskNumberInferer,
    ):
        """
        Initializes the BlockProcessor with required dependencies.

        Args:
            asset_downloader_factory (Callable): A callable that returns an AssetDownloader instance.
            processors (List[Any]): List of HTML processors to apply.
            metadata_extractor (MetadataExtractor): Component for extracting metadata.
            problem_builder (ProblemBuilder): Component for building Problem objects.
            task_inferer (TaskNumberInferer): Component for inferring task_number from KES codes.
        """
        self.asset_downloader_factory = asset_downloader_factory
        self.processors = processors
        self.metadata_extractor = metadata_extractor
        self.problem_builder = problem_builder
        self.task_inferer = task_inferer

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
        """
        logger.debug(f"Processing block {block_index}...")
        combined_soup = BeautifulSoup('', 'html.parser')
        combined_soup.append(qblock.extract())

        # Get downloader instance
        downloader = self.asset_downloader_factory(page, base_url, files_location_prefix)

        # Extract metadata from header_container
        metadata = self.metadata_extractor.extract(header_container)
        qblock_id = qblock.get('id', '')
        block_metadata = {
            "task_id": metadata["task_id"],
            "form_id": qblock_id,
            "block_index": block_index
        }
        extracted_task_id = metadata["task_id"] or f"unknown_{block_index}"

        # Initialize processors if not provided
        if not self.processors:
            processors_to_apply = [
                ImageScriptProcessor(),
                FileLinkProcessor(),
                TaskInfoProcessor(),
                InputFieldRemover(),
                MathMLRemover(),
                UnwantedElementRemover()
            ]
        else:
            processors_to_apply = self.processors

        # Process images inside <a> tags
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

        # Apply processors
        all_new_images = {}
        all_new_files = {}
        for processor in processors_to_apply:
            if hasattr(processor, 'process') and callable(processor.process):
                if processor.__class__.__name__ in ['ImageScriptProcessor', 'FileLinkProcessor']:
                    processed_soup, proc_metadata = processor.process(combined_soup, page_assets_dir.parent, downloader=downloader)
                else:
                    processed_soup, proc_metadata = processor.process(combined_soup, page_assets_dir.parent)
                combined_soup = processed_soup
                if isinstance(proc_metadata, dict):
                    all_new_images.update(proc_metadata.get('downloaded_images', {}))
                    all_new_files.update(proc_metadata.get('downloaded_files', {}))

        # Clean up
        for img_tag in combined_soup.find_all('img'):
            if img_tag.get('alt') == 'undefined' or img_tag.get('align') or img_tag.get('border'):
                img_tag.decompose()

        # Append task-header-panel
        task_header_panel = header_container.find('div', class_='task-header-panel')
        if task_header_panel:
            header_soup_temp = BeautifulSoup('', 'html.parser')
            header_soup_temp.append(task_header_panel)
            info_proc = next((p for p in processors_to_apply if isinstance(p, TaskInfoProcessor)), TaskInfoProcessor())
            processed_header_soup, _ = info_proc.process(header_soup_temp, page_assets_dir.parent)
            task_header_panel = processed_header_soup.find('div', class_='task-header-panel')
            combined_soup.append(task_header_panel.extract())

        # Remove scripts
        for script_tag in combined_soup.find_all('script'):
            script_tag.decompose()

        processed_html_string = str(combined_soup)
        assignment_text = combined_soup.get_text(separator='\n', strip=True)

        # === КРИТИЧЕСКИ ВАЖНАЯ ЧАСТЬ: ИЗВЛЕЧЕНИЕ КЭС И ИНФЕРЕНС НОМЕРА ЗАДАНИЯ ===
        kes_codes = self._extract_kes_codes_reliable(header_container)
        kos_codes = self._extract_kos_codes_reliable(header_container)
        answer_type = self._determine_answer_type(header_container)

        # Infer task_number using official specification
        task_number = self.task_inferer.infer(kes_codes, answer_type)

        # Build Problem
        problem_id = f"{page_num}_{extracted_task_id}"
        source_url = f"{base_url}?proj={proj_id}&page={page_num}"
        problem = self.problem_builder.build(
            problem_id=problem_id,
            subject="mathematics",
            type_str="short" if answer_type == "short" else "extended",
            text=assignment_text,
            topics=kes_codes,
            difficulty="basic",  # Will be overridden by spec if needed
            source_url=source_url,
            form_id=qblock_id,
            meta={"original_block_index": block_index, "proj_id": proj_id},
            task_number=task_number,
            kes_codes=kes_codes,
            kos_codes=kos_codes,
            exam_part="Part 1" if task_number <= 12 else "Part 2",
            max_score=1,  # Will be overridden by spec
            difficulty_level="basic"  # Will be overridden by spec
        )

        logger.debug(f"Finished processing block {block_index} with task_number={task_number}.")
        return processed_html_string, assignment_text, all_new_images, all_new_files, problem, block_metadata

    def _extract_kes_codes_reliable(self, header_container: Tag) -> List[str]:
        """Extracts KES codes reliably by parsing the structured 'КЭС:' line."""
        kes_div = header_container.find('div', string=re.compile(r'КЭС\s*:'))
        if not kes_div:
            return []
        # Get the next sibling which contains the codes
        next_sib = kes_div.next_sibling
        if not next_sib:
            return []
        text = next_sib.get_text() if hasattr(next_sib, 'get_text') else str(next_sib)
        # Extract patterns like "7.5", "2.1", etc.
        return re.findall(r'\b\d+(?:\.\d+)*\b', text)

    def _extract_kos_codes_reliable(self, header_container: Tag) -> List[str]:
        """Extracts KOS codes reliably by parsing the structured 'КОС:' line."""
        kos_div = header_container.find('div', string=re.compile(r'КОС\s*:'))
        if not kos_div:
            return []
        next_sib = kos_div.next_sibling
        if not next_sib:
            return []
        text = next_sib.get_text() if hasattr(next_sib, 'get_text') else str(next_sib)
        return re.findall(r'\b\d+(?:\.\d+)*\b', text)

    def _determine_answer_type(self, header_container: Tag) -> str:
        """Determines answer type from the 'Тип ответа:' line."""
        type_div = header_container.find('div', string=re.compile(r'Тип ответа\s*:'))
        if not type_div:
            return "unknown"
        next_sib = type_div.next_sibling
        if not next_sib:
            return "unknown"
        text = next_sib.get_text() if hasattr(next_sib, 'get_text') else str(next_sib)
        if "Развёрнутый" in text or "Развернутый" in text:
            return "extended"
        return "short"
