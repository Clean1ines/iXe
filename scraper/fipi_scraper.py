"""
Module for scraping data from the FIPI website.

This module provides the `FIPIScraper` class which handles interactions with the
FIPI website using Playwright to fetch subject listings and assignment pages.
"""

import logging # NEW: Import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple # MODIFIED: Added Tuple
from bs4 import BeautifulSoup
from bs4 import Tag # NEW: Import Tag
from playwright.sync_api import sync_playwright
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

logger = logging.getLogger(__name__) # NEW: Create module logger

class FIPIScraper:
    """
    A class to scrape assignment data from the FIPI website.

    This class uses Playwright to interact with the website, fetch pages,
    and extract relevant information like subject listings and assignment content.
    """

    def __init__(self, base_url: str, subjects_url: str = None, user_agent: str = None, headless: bool = True):
        """
        Initializes the FIPIScraper.

        Args:
            base_url (str): The base URL for assignment pages (e.g., .../questions.php).
            subjects_url (str, optional): The URL for the subjects listing page.
                                          If not provided, defaults to base_url.
            user_agent (str, optional): User agent string for the browser session.
                                        Defaults to None, which uses the system default or a predefined one.
            headless (bool, optional): Whether to run the browser in headless mode.
                                       Defaults to True.
        """
        self.base_url = base_url
        self.subjects_url = subjects_url if subjects_url else base_url
        self.user_agent = user_agent
        self.headless = headless

    def get_projects(self) -> Dict[str, str]:
        """
        Fetches the list of available subjects and their project IDs from the FIPI website.

        This method navigates to the subjects_url, finds the list of subjects (typically within
        a <ul> element with an ID like 'pgp_...'), parses the list items (<li>), and
        extracts the project ID (often from an 'id' attribute like 'p_...') and the subject name.

        Returns:
            Dict[str, str]: A dictionary mapping project IDs (str) to subject names (str).
                            Example: {'AC437B...': 'Математика. Профильный уровень', ...}
                            Returns an empty dict if the list is not found or parsing fails.
        """
        print(f"[Fetching subjects] Navigating to {self.subjects_url} ...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=self.user_agent, ignore_https_errors=True)
            page = context.new_page()
            page.goto(self.subjects_url, wait_until="networkidle")

            projects = {}
            try:
                list_selector = "ul[id^='pgp_']"
                list_element = page.query_selector(list_selector)

                if list_element:
                    list_items = list_element.query_selector_all("li[id^='p_']")
                    for item in list_items:
                        item_id = item.get_attribute("id")
                        if item_id and item_id.startswith("p_"):
                            proj_id = item_id[2:]
                        else:
                            print(f"Warning: Skipping item with unexpected ID format: {item_id}")
                            continue

                        subject_name = item.inner_text().strip()
                        if proj_id and subject_name:
                            projects[proj_id] = subject_name
                        else:
                            print(f"Warning: Skipping item with empty ID or name: {item_id}, Name: '{subject_name}'")
            except Exception as e:
                print(f"Error parsing projects list: {e}")
            finally:
                browser.close()

        print(f"[Fetched subjects] Found {len(projects)} subjects.")
        return projects

    def _extract_task_id(self, header_container) -> str:
        """
        Извлекает task_id из контейнера заголовка.
        """
        task_id = ""
        canselect_span = header_container.find('span', class_='canselect')
        if canselect_span:
            task_id = canselect_span.get_text(strip=True)
        return task_id

    def _extract_kes_codes(self, header_container) -> List[str]:
        """
        Извлекает коды КЭС из контейнера заголовка.
        """
        kes_codes = []
        kes_text = header_container.get_text(separator=' ', strip=True)
        # Пример: ищем последовательности вида "A1.2", "B3.4", "1.2.3"
        kes_pattern = re.compile(r'\b[A-Z]?\d+(?:\.\d+)*\b')
        kes_codes = kes_pattern.findall(kes_text)
        return kes_codes

    def _determine_task_type_and_difficulty(self, header_container) -> Tuple[str, str]:
        """
        Определяет тип и сложность задания на основе номера задания в заголовке.
        """
        type_str = "unknown"
        difficulty_str = "unknown"
        header_text = header_container.get_text(separator=' ', strip=True)
        # Пример: ищем начало строки с номером, например "Задание 1", "1", "A1", "B2"
        match = re.search(r'(?:Задание\s+)?([A-Z]?\d+)', header_text)
        if match:
            task_num = match.group(1)
            # Простая логика, можно улучшить
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
                # Только цифра
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
                print(f"Warning: Unpaired element found at index {i}: {ordered_elements[i][0]}")
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

    def _process_single_block(self, header_container: Tag, qblock: Tag, block_index: int, page_num: str, page_assets_dir: Path, downloader: AssetDownloader) -> Tuple[str, str, Dict[str, str], Dict[str, str]]:
        """
        Processes a single pair of (header_container, qblock) elements.

        This involves applying various HTML processors (ImageScriptProcessor, FileLinkProcessor, etc.),
        downloading associated assets (images, files), removing unwanted elements,
        and extracting the final processed HTML and text content.

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
                - new_images_dict (Dict[str, str]): A map of original image URLs to local paths downloaded in this block.
                - new_files_dict (Dict[str, str]): A map of original file URLs to local paths downloaded in this block.
        """
        logger.debug(f"Processing block {block_index}...")
        # Initialize all processors including UnwantedElementRemover
        image_proc = ImageScriptProcessor(downloader)
        file_proc = FileLinkProcessor(downloader)
        info_proc = TaskInfoProcessor()
        input_remover = InputFieldRemover()
        math_remover = MathMLRemover()
        unwanted_remover = UnwantedElementRemover()

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
                        img_relative_path_from_html = local_img_path.relative_to(page_assets_dir.parent) # relative to page dir
                        img_tag['src'] = str(img_relative_path_from_html)
                        logger.debug(f"Updated img src inside <a> to local file: {img_tag['src']}")
                    else:
                        logger.warning(f"Failed to download image {clean_img_src} for assignment pair {block_index} on page {page_num}.")

        # Apply all processors
        combined_soup, new_imgs = image_proc.process(combined_soup, page_assets_dir.parent) # pass page dir to processor
        combined_soup, new_files = file_proc.process(combined_soup, page_assets_dir.parent) # pass page dir to processor
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
            print(f"Warning: No task-header-panel found in header container for assignment pair {block_index}")

        # Apply UnwantedElementRemover AFTER extracting task_id/form_id
        combined_soup = unwanted_remover.process(combined_soup)

        # Remove all remaining scripts
        for script_tag in combined_soup.find_all('script'):
            script_tag.decompose()

        processed_html_string = str(combined_soup)
        assignment_text = combined_soup.get_text(separator='\n', strip=True)

        logger.debug(f"Finished processing block {block_index}.")
        return processed_html_string, assignment_text, new_imgs, new_files


    def scrape_page(self, proj_id: str, page_num: str, run_folder: Path) -> Tuple[List[Problem], Dict[str, Any]]:
        """
        Scrapes a specific page of assignments for a given subject using a full set of HTML processors,
        including removal of unwanted UI elements.

        This method uses dedicated processor classes for different aspects of HTML processing:
        - ImageScriptProcessor: replaces ShowPicture(...) scripts with <img> tags
        - FileLinkProcessor: downloads and localizes file links
        - TaskInfoProcessor: updates info button handlers
        - InputFieldRemover: removes answer input fields
        - MathMLRemover: strips MathML for MathJax compatibility
        - UnwantedElementRemover: removes auxiliary UI elements like hints, status spans, and unused table rows

        It also calls the _pair_elements method to find and pair header and qblock elements.

        Args:
            proj_id (str): The project ID corresponding to the subject.
            page_num (str): The page number to scrape (e.g., 'init', '1', '2').
            run_folder (Path): The base run folder where assets should be saved.

        Returns:
            Tuple[List[Problem], Dict[str, Any]]: A tuple containing:
                - A list of Problem objects created from the scraped data.
                - A dictionary with the old scraped data structure (page_name, blocks_html, etc.).
        """
        page_url = f"{self.base_url}?proj={proj_id}&page={page_num}"
        logger.info(f"Scraping page {page_num} for project {proj_id}, URL: {page_url}") # NEW: Use logger

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=self.user_agent, ignore_https_errors=True)
            page = context.new_page()
            page.goto(page_url, wait_until="networkidle")
            page.wait_for_timeout(3000)

            try:
                files_location_prefix = page.evaluate("window.files_location || '../../'")
            except Exception as e:
                print(f"Warning: Could not get files_location from page {page_url}, using default. Error: {e}")
                files_location_prefix = '../../'

            downloader = AssetDownloader(page, self.base_url, files_location_prefix)
            page_content = page.content()
            page_soup = BeautifulSoup(page_content, 'html.parser')

            # NEW: Call _pair_elements to get paired header and qblock elements
            paired_elements = self._pair_elements(page_soup)
            logger.info(f"Found and paired {len(paired_elements)} header-qblock sets on page {page_num}.") # MODIFIED: Use logger and refer to pairs

            processed_blocks_html = []
            assignments_text = []
            downloaded_images = {}
            downloaded_files = {}
            task_metadata: List[Dict[str, str]] = []

            page_assets_dir = run_folder / page_num / "assets"
            page_assets_dir.mkdir(parents=True, exist_ok=True)

            problems: List[Problem] = []

            for idx, (header_container, qblock) in enumerate(paired_elements):
                # NEW: Extract metadata using the new method
                metadata = self._extract_metadata_for_block(header_container)

                task_metadata.append({
                    "task_id": metadata['task_id'],
                    "form_id": metadata['form_id'],
                    "block_index": idx
                })

                # NEW: Process the block using the new method
                processed_html, assignment_text, new_images, new_files = self._process_single_block(
                    header_container, qblock, idx, page_num, page_assets_dir, downloader
                )
                processed_blocks_html.append(processed_html)
                assignments_text.append(assignment_text)
                downloaded_images.update(new_images)
                downloaded_files.update(new_files)

                # --- Создание объекта Problem ---
                # Извлекаем данные из обработанного combined_soup и header_container
                extracted_task_id = metadata['task_id'] or f"unknown_{idx}"
                problem_id = f"{page_num}_{extracted_task_id}"

                # Определяем subject, type, difficulty
                # subject: передаётся в scrape_page, но пока используем заглушку
                subject = "unknown_subject" # TODO: передать subject сюда или получить из proj_id
                type_str, difficulty_str = self._determine_task_type_and_difficulty(header_container)

                # Извлекаем темы (КЭС)
                topics = self._extract_kes_codes(header_container)

                # Создаём объект Problem
                problem = Problem(
                    problem_id=problem_id,
                    subject=subject,
                    type=type_str,
                    text=assignment_text,
                    options=None, # Пока не извлекаем
                    answer="placeholder_answer", # Пока не извлекаем
                    solutions=None,
                    topics=topics,
                    skills=None, # Пока не извлекаем
                    difficulty=difficulty_str,
                    source_url=page_url,
                    raw_html_path=None, # Пока не сохраняем
                    created_at=datetime.now(),
                    updated_at=None,
                    metadata={"original_block_index": idx, "proj_id": proj_id}
                )
                problems.append(problem)
                # --- Конец создания Problem ---

            logger.info(f"Successfully processed {len(processed_blocks_html)} blocks for page {page_num}.") # NEW: Log success at end of method
            browser.close()

            scraped_data = {
                "page_name": page_num,
                "url": page_url,
                "assignments": assignments_text,
                "blocks_html": processed_blocks_html,
                "images": downloaded_images,
                "files": downloaded_files,
                "task_metadata": task_metadata
            }

            return problems, scraped_data
