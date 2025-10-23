# scraper/fipi_scraper.py
"""
Module for scraping data from the FIPI website.

This module provides the `FIPIScraper` class which handles interactions with the
FIPI website using Playwright to fetch subject listings and assignment pages.
"""

import re
from pathlib import Path
from typing import Dict, Any
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from utils.downloader import AssetDownloader
from processors.html_data_processors import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover  # <-- Убедились, что импорт присутствует
)


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

    def scrape_page(self, proj_id: str, page_num: str, run_folder: Path) -> Dict[str, Any]:
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

        Args:
            proj_id (str): The project ID corresponding to the subject.
            page_num (str): The page number to scrape (e.g., 'init', '1', '2').
            run_folder (Path): The base run folder where assets should be saved.

        Returns:
            Dict[str, Any]: A dictionary containing the scraped and processed data.
                            Example structure:
                            {
                                "page_name": page_num,
                                "url": "full_url_of_the_page",
                                "assignments": ["Text of assignment 1", ...],
                                "blocks_html": ["<div>Combined HTML for block 1</div>", ...],
                                "images": {"original_src": "local_path", ...},
                                "files": {"original_href": "local_path", ...}
                            }
        """
        page_url = f"{self.base_url}?proj={proj_id}&page={page_num}"
        print(f"[Scraping page: {page_num}] Fetching {page_url} ...")

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

            qblocks = page_soup.find_all('div', class_='qblock')
            header_containers = page_soup.find_all('div', id=re.compile(r'^i'))

            print(f"Found {len(qblocks)} qblocks and {len(header_containers)} header containers on page {page_num}.")

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

            print(f"Paired {len(paired_elements)} header-qblock sets.")

            # Initialize all processors including UnwantedElementRemover
            image_proc = ImageScriptProcessor(downloader)
            file_proc = FileLinkProcessor(downloader)
            info_proc = TaskInfoProcessor()
            input_remover = InputFieldRemover()
            math_remover = MathMLRemover()
            unwanted_remover = UnwantedElementRemover()

            processed_blocks_html = []
            assignments_text = []
            downloaded_images = {}
            downloaded_files = {}

            page_assets_dir = run_folder / page_num / "assets"
            page_assets_dir.mkdir(parents=True, exist_ok=True)

            for idx, (header_container, qblock) in enumerate(paired_elements):
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
                                downloaded_images[clean_img_src] = str(local_img_path.relative_to(run_folder / page_num))
                                img_relative_path_from_html = local_img_path.relative_to(run_folder / page_num)
                                img_tag['src'] = str(img_relative_path_from_html)
                                print(f"Updated img src inside <a> to local file: {img_tag['src']}")

                # Apply all processors
                combined_soup, new_imgs = image_proc.process(combined_soup, run_folder / page_num)
                combined_soup, new_files = file_proc.process(combined_soup, run_folder / page_num)
                combined_soup = input_remover.process(combined_soup)
                combined_soup = math_remover.process(combined_soup)
                downloaded_images.update(new_imgs)
                downloaded_files.update(new_files)

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
                    combined_soup.append(task_header_panel.extract())
                    print(f"Appended task-header-panel for assignment pair {idx}")
                else:
                    print(f"Warning: No task-header-panel found in header container for assignment pair {idx}")

                # 🔥 Ключевое изменение: применяем UnwantedElementRemover
                combined_soup = unwanted_remover.process(combined_soup)

                # Remove all remaining scripts
                for script_tag in combined_soup.find_all('script'):
                    script_tag.decompose()

                processed_html = str(combined_soup)
                processed_blocks_html.append(processed_html)
                assignments_text.append(combined_soup.get_text(separator='\n', strip=True))

            browser.close()

            return {
                "page_name": page_num,
                "url": page_url,
                "assignments": assignments_text,
                "blocks_html": processed_blocks_html,
                "images": downloaded_images,
                "files": downloaded_files
            }