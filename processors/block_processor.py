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
        task_inferer: Optional[TaskNumberInferer],
    ):
        """
        Initializes the BlockProcessor with required dependencies.

        Args:
            asset_downloader_factory (Callable): A callable that returns an AssetDownloader instance.
                                                 Expected signature: (page, base_url, files_location_prefix) -> AssetDownloader.
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

    async def process(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        page_num: str,
        page_assets_dir: Path,
        proj_id: str,
        base_url: str,
        subject: str,
        page: Any = None, # This is the Playwright page object
        files_location_prefix: str = "../../"
    ) -> Tuple[str, str, Dict[str, str], Dict[str, str], Problem, Dict[str, Any]]:
        """
        Processes a single block pair (header_container, qblock).
        """
        logger.debug(f"Processing block {block_index}...")
        combined_soup = BeautifulSoup('', 'html.parser')
        combined_soup.append(qblock.extract())

        # Create AssetDownloader instance using the page object passed to this method
        # This ensures the page is available when download is called
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

        # Process images inside <a> tags - construct full URL here
        for a_tag in combined_soup.find_all('a'):
            img_tag = a_tag.find('img')
            if img_tag:
                img_src = img_tag.get('src') or img_tag.get('data-src')
                if img_src:
                    # Construct full asset URL in BlockProcessor
                    full_asset_path = files_location_prefix + img_src
                    asset_url = urljoin(base_url, full_asset_path)
                    # Check if download method is async
                    if hasattr(downloader, 'download') and asyncio.iscoroutinefunction(downloader.download):
                        local_img_path = await downloader.download(asset_url, page_assets_dir / "assets", asset_type='image')
                    else:
                        local_img_path = downloader.download(asset_url, page_assets_dir / "assets", asset_type='image')
                    if local_img_path:
                        img_relative_path_from_html = local_img_path.relative_to(page_assets_dir)
                        img_tag['src'] = str(img_relative_path_from_html)

        # Apply processors
        all_new_images = {}
        all_new_files = {}
        for processor in processors_to_apply:
            if hasattr(processor, 'process') and callable(processor.process):
                if processor.__class__.__name__ in ['ImageScriptProcessor', 'FileLinkProcessor']:
                    # Pass the constructed base URL and prefix to processors that need them
                    # For async processors, use await; for sync, call directly
                    if hasattr(processor.process, '__await__') or asyncio.iscoroutinefunction(processor.process):
                        processed_soup, proc_metadata = await processor.process(
                            combined_soup, 
                            page_assets_dir.parent, 
                            downloader=downloader, 
                            base_url=base_url, 
                            files_location_prefix=files_location_prefix
                        )
                    else:
                        processed_soup, proc_metadata = processor.process(
                            combined_soup, 
                            page_assets_dir.parent, 
                            downloader=downloader, 
                            base_url=base_url, 
                            files_location_prefix=files_location_prefix
                        )
                else:
                    # All processors are now async, so we can safely await all of them
                    processed_soup, proc_metadata = await processor.process(combined_soup, page_assets_dir.parent)
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
            # Since TaskInfoProcessor is now async, we need to await its process method
            processed_header_soup, _ = await info_proc.process(header_soup_temp, page_assets_dir.parent)
            task_header_panel = processed_header_soup.find('div', class_='task-header-panel')
            combined_soup.append(task_header_panel.extract())

        # Remove scripts
        for script_tag in combined_soup.find_all('script'):
            script_tag.decompose()

        processed_html_string = str(combined_soup)
        assignment_text = combined_soup.get_text(separator='\n', strip=True)

        # === ИЗВЛЕЧЕНИЕ КЭС И ИНФЕРЕНС НОМЕРА ЗАДАНИЯ ===
        kes_codes = self._extract_kes_codes_reliable(header_container)
        kos_codes = self._extract_kos_codes_reliable(header_container)
        answer_type = self._determine_answer_type(header_container)

        # Check if task_inferer is available before calling infer
        task_number = 0
        difficulty_level = 'basic'
        max_score = 1
        type_str = 'short' if answer_type == 'short' else 'extended'
        
        if self.task_inferer is not None:
            try:
                # Try the original signature
                task_number = self.task_inferer.infer(kes_codes, answer_type) or 0
                difficulty_level = 'basic' if task_number <= 12 else 'advanced'
                max_score = 1 if task_number <= 12 else 2
                type_str = 'short' if answer_type == 'short' else 'extended'
            except TypeError as e:
                # Fall back to the new signature if the original fails
                try:
                    inference_result = self.task_inferer.infer(kes_codes, answer_type) or 0
                    if isinstance(inference_result, dict):
                        task_number = inference_result.get('task_number', None) or 0
                        difficulty_level = inference_result.get('difficulty_level', 'basic')
                        max_score = inference_result.get('max_score', 1)
                        type_str = inference_result.get('type_str', 'short' if answer_type == 'short' else 'extended')
                    else:
                        # Fallback if inference_result is an int
                        task_number = int(inference_result) if inference_result is not None else 0
                        difficulty_level = 'basic' if task_number <= 12 else 'advanced'
                        max_score = 1 if task_number <= 12 else 2
                        type_str = 'short' if answer_type == 'short' else 'extended'
                except Exception as e2:
                    logger.error(f"Both infer signatures failed for block {block_index}: {e2}. Using defaults.")
        else:
            logger.warning(f"BlockProcessor.task_inferer is None, using default values for block {block_index}.")

        # Build Problem
        problem_id = f"{page_num}_{extracted_task_id}"
        source_url = f"{base_url}?proj={proj_id}&page={page_num}"
        problem = self.problem_builder.build(
            problem_id=problem_id,
            subject=subject,
            type_str=type_str,
            text=assignment_text,
            topics=kes_codes,
            source_url=source_url,
            form_id=qblock_id,
            meta={"original_block_index": block_index, "proj_id": proj_id},
            task_number=task_number,
            kes_codes=kes_codes,
            kos_codes=kos_codes,
            exam_part="Part 1" if task_number <= 12 else "Part 2",
            max_score=max_score,
            difficulty_level=difficulty_level
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
