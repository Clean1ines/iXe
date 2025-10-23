# scraper/fipi_scraper.py
"""
Module for scraping data from the FIPI website.

This module provides the `FIPIScraper` class which handles interactions with the
FIPI website using Playwright to fetch subject listings and assignment pages.
"""

import re
import zipfile
from pathlib import Path
from typing import Dict, List, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from utils.downloader import AssetDownloader


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
        # Use subjects_url if provided, otherwise assume base_url is also the subjects page
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
                # Find the main list element containing subjects
                # This ID is based on the example provided in the prompt
                list_selector = "ul[id^='pgp_']"
                list_element = page.query_selector(list_selector)

                if list_element:
                    # Find all list items within the found list
                    list_items = list_element.query_selector_all("li[id^='p_']")
                    for item in list_items:
                        # Extract project ID from the 'id' attribute (e.g., p_XXXX -> XXXX)
                        item_id = item.get_attribute("id")
                        if item_id and item_id.startswith("p_"):
                            proj_id = item_id[2:]  # Remove the 'p_' prefix
                        else:
                            print(f"Warning: Skipping item with unexpected ID format: {item_id}")
                            continue # Skip if ID doesn't match expected format

                        # Extract subject name from the text content
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

    def scrape_page_refactored(self, proj_id: str, page_num: str, run_folder: Path) -> Dict[str, Any]:
        """
        Scrapes a specific page of assignments for a given subject (refactored version).

        This is a refactored version that uses AssetDownloader for downloading assets
        instead of the internal _download_asset_with_context method.

        Args:
            proj_id (str): The project ID corresponding to the subject.
            page_num (str): The page number to scrape (e.g., 'init', '1', '2').
            run_folder (Path): The base run folder where assets should be saved.

        Returns:
            Dict[str, Any]: A dictionary containing the scraped and processed data.
        """
        page_url = f"{self.base_url}?proj={proj_id}&page={page_num}"
        print(f"[Scraping page: {page_num}] Fetching {page_url} ...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=self.user_agent, ignore_https_errors=True)
            page = context.new_page()
            page.goto(page_url, wait_until="networkidle")
            # Allow dynamic content to load
            # Consider replacing with more specific wait conditions if possible
            page.wait_for_timeout(3000)

            try:
                # Get the prefix for image/file paths from the page's JS context
                files_location_prefix = page.evaluate("window.files_location || '../../'")
            except Exception as e:
                print(f"Warning: Could not get files_location from page {page_url}, using default. Error: {e}")
                files_location_prefix = '../../'

            # Initialize AssetDownloader
            downloader = AssetDownloader(page, self.base_url, files_location_prefix)

            # Get the full HTML of the page body to work with the order of elements
            page_content = page.content()
            page_soup = BeautifulSoup(page_content, 'html.parser')

            # Find all qblock elements and divs with id starting with 'i'
            qblocks = page_soup.find_all('div', class_='qblock')
            header_containers = page_soup.find_all('div', id=re.compile(r'^i')) # Find divs with id starting with 'i'

            print(f"Found {len(qblocks)} qblocks and {len(header_containers)} header containers on page {page_num}.")

            # Pair qblocks with their corresponding header containers based on DOM order
            # This assumes that the first header_container corresponds to the first qblock, etc.
            # The total number of elements should ideally be len(qblocks) + len(header_containers)
            # and they should alternate or be grouped predictably.
            # We iterate through the direct children of the body (or a common parent if applicable)
            # to establish the order and pairing.
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

            # Now, pair them based on the established order
            # We expect a pattern like: header, qblock, header, qblock, ...
            paired_elements = []
            i = 0
            while i < len(ordered_elements):
                if ordered_elements[i][0] == 'header' and i + 1 < len(ordered_elements) and ordered_elements[i + 1][0] == 'qblock':
                    # Found a pair: header, qblock
                    header_soup = ordered_elements[i][1]
                    qblock_soup = ordered_elements[i + 1][1]
                    paired_elements.append((header_soup, qblock_soup))
                    i += 2
                elif ordered_elements[i][0] == 'qblock' and i + 1 < len(ordered_elements) and ordered_elements[i + 1][0] == 'header':
                    # Found a pair: qblock, header (order might vary)
                    qblock_soup = ordered_elements[i][1]
                    header_soup = ordered_elements[i + 1][1]
                    paired_elements.append((header_soup, qblock_soup))
                    i += 2
                else:
                    # Handle unpaired elements if necessary, or skip
                    print(f"Warning: Unpaired element found at index {i}: {ordered_elements[i][0]}")
                    i += 1

            print(f"Paired {len(paired_elements)} header-qblock sets.")

            processed_blocks_html = []
            assignments_text = []
            downloaded_images = {} # Map original src to local path
            downloaded_files = {} # Map original href to local path

            # Create assets directory for this specific page
            page_assets_dir = run_folder / page_num / "assets"
            page_assets_dir.mkdir(parents=True, exist_ok=True)

            for idx, (header_container, qblock) in enumerate(paired_elements):
                # Create a new soup object to hold the combined content for this specific assignment
                combined_soup = BeautifulSoup('', 'html.parser')
                # Append the qblock first
                combined_soup.append(qblock.extract()) # extract() removes it from original tree

                # --- Process Images (ShowPicture, ShowPictureQ2WH) ---
                # ИСПРАВЛЕНО: Ищем оба типа вызовов, но обрабатываем только те, которые должны создать <img>
                # В оригинальном скрипте `ShowPicture` вызывает `ShowPictureQ2WH`, которая создает <img> внутри <a>
                # Мы будем искать скрипты, вызывающие `ShowPictureQ2WH` или `ShowPicture` (предполагая, что они создают <img>)
                # и заменять их на <img> теги, скачивая изображение.
                # Теперь они могут быть в qblock (внутри combined_soup после добавления).
                for script_tag in combined_soup.find_all('script', string=re.compile(r'ShowPicture\w*\s*\(\s*[\'\"][^\'\"]+[\'\"]', re.IGNORECASE)):
                    script_text = script_tag.get_text()
                    # Попробуем оба паттерна
                    match_q2wh = re.search(r"ShowPictureQ2WH\s*\(\s*['\"]([^'\"]+)['\"]", script_text, re.IGNORECASE)
                    match_gen = re.search(r"ShowPicture\w*\s*\(\s*['\"]([^'\"]+)['\"]", script_text, re.IGNORECASE)

                    img_src = None
                    if match_q2wh:
                        img_src = match_q2wh.group(1)
                        print(f"Found ShowPictureQ2WH call, image src: {img_src}")
                    elif match_gen and not match_q2wh: # Если не Q2WH, но другая функция
                        img_src = match_gen.group(1)
                        print(f"Found ShowPicture call, image src: {img_src}")

                    if img_src:
                        # Download image and get local path using AssetDownloader
                        local_path = downloader.download(img_src, page_assets_dir, asset_type='image')
                        if local_path:
                            # ИСПРАВЛЕНО: Сохраняем путь ОТНОСИТЕЛЬНО папки страницы (где будет лежать HTML)
                            downloaded_images[img_src] = str(local_path.relative_to(run_folder / page_num)) # Стало: относительно папки страницы
                            # Create new <img> tag with local path RELATIVE TO THE HTML FILE'S DIRECTORY
                            # The HTML file will be saved as run_folder / page_num / f"{page_num}.html"
                            # So, the img src should be e.g. "assets/filename.jpg"
                            img_relative_path_from_html = local_path.relative_to(run_folder / page_num) # Path object
                            new_img = combined_soup.new_tag('img', src=str(img_relative_path_from_html), alt='Downloaded FIPI Image')
                            # Replace the <script> tag with the <img> tag
                            script_tag.replace_with(new_img)
                            print(f"Replaced script with img tag: {new_img}")


                # --- Process Images inside <a> tags (often created by ShowPictureQ2WH) ---
                # Find <img> tags inside <a> tags that might be previews for downloads
                # These often have src="../../docs/.../simg1_...gif" (small preview)
                # The ShowPictureQ2WH function might create the <img> directly inside the <a>
                # We process them *after* handling the scripts above, so the <img> tags exist in soup
                for a_tag in combined_soup.find_all('a'):
                    img_tag = a_tag.find('img')
                    if img_tag:
                        # Get the src of the image, assuming it's relative like the file links
                        img_src = img_tag.get('src')
                        if img_src:
                            # Clean up the src path if it starts with ../../
                            clean_img_src = img_src.lstrip('../../')
                            local_img_path = downloader.download(clean_img_src, page_assets_dir, asset_type='image')
                            if local_img_path:
                                # ИСПРАВЛЕНО: Сохраняем путь ОТНОСИТЕЛЬНО папки страницы
                                downloaded_images[clean_img_src] = str(local_img_path.relative_to(run_folder / page_num)) # Стало
                                # Update the img src to point to the local file RELATIVE TO THE HTML FILE'S DIRECTORY
                                img_relative_path_from_html = local_img_path.relative_to(run_folder / page_num) # Path object
                                img_tag['src'] = str(img_relative_path_from_html)
                                print(f"Updated img src inside <a> to local file: {img_tag['src']}")


                # --- Process Files (e.g., .zip from links) ---
                # Find links that might trigger file downloads via javascript or direct href
                for a_tag in combined_soup.find_all('a'):
                    href = a_tag.get('href')
                    # Извлекаем путь из javascript: ссылки, если необходимо
                    file_path = href
                    if href and href.startswith('javascript:'):
                        # Example: javascript:var wnd=window.open('../../docs/.../file.zip',...
                        match = re.search(r"window\.open\(\s*['\"]([^'\"]+\.zip|[^'\"]+\.rar|[^'\"]+\.pdf|doc|docx|xls|xlsx)['\"]", href, re.I)
                        if match:
                            file_path = match.group(1)
                            # Remove leading ../../ if present, as it's relative to base_url
                            file_path = file_path.lstrip('../../')
                    # Check if file_path is likely a file path
                    if file_path and re.search(r'\.(zip|rar|pdf|doc|docx|xls|xlsx)$', file_path, re.I):
                        # Attempt download using AssetDownloader
                        local_path = downloader.download(file_path, page_assets_dir, asset_type='file')
                        if local_path:
                            # ИСПРАВЛЕНО: Сохраняем путь ОТНОСИТЕЛЬНО папки страницы
                            downloaded_files[file_path] = str(local_path.relative_to(run_folder / page_num)) # Стало
                            # Update the href in the link to point to the local file RELATIVE TO THE HTML FILE'S DIRECTORY
                            file_relative_path_from_html = local_path.relative_to(run_folder / page_num) # Path object
                            a_tag['href'] = str(file_relative_path_from_html)
                            print(f"Updated link href to local file: {a_tag['href']}")


                # --- Remove duplicate or undefined <img> tags based on attributes ---
                for img_tag in combined_soup.find_all('img'):
                    if img_tag.get('alt') == 'undefined' or img_tag.get('align') or img_tag.get('border'):
                        img_tag.decompose()

                # --- Remove the original answer input field from FIPI HTML ---
                # ИСПРАВЛЕНО: Удаляем поле ввода ответа, которое было на сайте FIPI
                # Теперь ищем внутри combined_soup (всего фрагмента задания)
                for input_tag in combined_soup.find_all('input', attrs={'name': 'answer'}):
                    input_tag.decompose() # Удаляем элемент из дерева BeautifulSoup
                    print(f"Removed original FIPI answer input field: {input_tag}")


                # --- Append the header container (task-header-panel) after the qblock ---
                # Extract the task-header-panel from the header_container
                task_header_panel = header_container.find('div', class_='task-header-panel')
                if task_header_panel:
                    # Modify the onclick attribute to work in the standalone HTML for the info button INSIDE the panel
                    info_button = task_header_panel.find('div', class_='info-button')
                    if info_button:
                         # Modify the onclick attribute to work in the standalone HTML
                        # The original onclick="this.parentNode.classList.toggle("show-info")" might not work as expected
                        # when the HTML is saved separately. We'll add a generic JS function call.
                        # ИСПРАВЛЕНО: Обновляем onclick у кнопки info_button внутри панели
                        info_button['onclick'] = f"toggleInfo(this); return false;" # Add return false to prevent any default action
                        print(f"Found and processed info button for assignment pair {idx}")
                    # Append the task-header-panel to the combined soup
                    combined_soup.append(task_header_panel.extract()) # extract() removes it from header_container
                    print(f"Appended task-header-panel for assignment pair {idx}")
                else:
                    print(f"Warning: No task-header-panel found in header container for assignment pair {idx}")


                # --- Clean up remaining scripts and MathML ---
                # ИСПРАВЛЕНО: Возвращаем удаление MathML тегов, как в оригинальном скрипте
                # Это позволяет MathJax обрабатывать оставшиеся формулы (LaTeX и т.п.).
                for math_tag in combined_soup.find_all(['math','mml:math']):
                    math_tag.decompose()
                # Удаляем все скрипты, кроме тех, что были обработаны выше.
                # Те, что были обработаны, уже заменены и не находятся тут.
                for s in combined_soup.find_all('script'):
                    # Удаляем все оставшиеся скрипты, которые не были обработаны выше.
                    # Те, что были обработаны, уже заменены и не находятся тут.
                    s.decompose() # Удаляем все оставшиеся скрипты


                processed_html = str(combined_soup)
                processed_blocks_html.append(processed_html)
                assignments_text.append(combined_soup.get_text(separator='\n', strip=True))

            browser.close() # Close browser after scraping

            return {
                "page_name": page_num,
                "url": page_url,
                "assignments": assignments_text,
                "blocks_html": processed_blocks_html, # Теперь содержит объединённый HTML для каждой пары
                "images": downloaded_images,
                "files": downloaded_files
            }

    def scrape_page(self, proj_id: str, page_num: str, run_folder: Path) -> Dict[str, Any]:
        """
        Scrapes a specific page of assignments for a given subject.

        This method navigates to the URL for a specific page (proj_id & page_num),
        extracts assignment blocks (`div.qblock`) and their associated headers (`div[id^='i']`).
        It pairs them based on their order in the DOM, processes their content,
        downloads images and files, and returns the processed data.

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
                                "assignments": ["Text of assignment 1", "Text of assignment 2", ...],
                                "blocks_html": ["<div>Combined HTML for block 1</div>", ...],
                                "images": {"original_src": "local_path", ...}, # Map of image sources to saved paths
                                "files": {"original_href": "local_path", ...} # Map of file sources to saved paths
                            }
                            Returns an empty dict or raises an exception if scraping fails critically.
        """
        page_url = f"{self.base_url}?proj={proj_id}&page={page_num}"
        print(f"[Scraping page: {page_num}] Fetching {page_url} ...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=self.user_agent, ignore_https_errors=True)
            page = context.new_page()
            page.goto(page_url, wait_until="networkidle")
            # Allow dynamic content to load
            # Consider replacing with more specific wait conditions if possible
            page.wait_for_timeout(3000)

            try:
                # Get the prefix for image/file paths from the page's JS context
                files_location_prefix = page.evaluate("window.files_location || '../../'")
            except Exception as e:
                print(f"Warning: Could not get files_location from page {page_url}, using default. Error: {e}")
                files_location_prefix = '../../'

            # Get the full HTML of the page body to work with the order of elements
            page_content = page.content()
            page_soup = BeautifulSoup(page_content, 'html.parser')

            # Find all qblock elements and divs with id starting with 'i'
            qblocks = page_soup.find_all('div', class_='qblock')
            header_containers = page_soup.find_all('div', id=re.compile(r'^i')) # Find divs with id starting with 'i'

            print(f"Found {len(qblocks)} qblocks and {len(header_containers)} header containers on page {page_num}.")

            # Pair qblocks with their corresponding header containers based on DOM order
            # This assumes that the first header_container corresponds to the first qblock, etc.
            # The total number of elements should ideally be len(qblocks) + len(header_containers)
            # and they should alternate or be grouped predictably.
            # We iterate through the direct children of the body (or a common parent if applicable)
            # to establish the order and pairing.
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

            # Now, pair them based on the established order
            # We expect a pattern like: header, qblock, header, qblock, ...
            paired_elements = []
            i = 0
            while i < len(ordered_elements):
                if ordered_elements[i][0] == 'header' and i + 1 < len(ordered_elements) and ordered_elements[i + 1][0] == 'qblock':
                    # Found a pair: header, qblock
                    header_soup = ordered_elements[i][1]
                    qblock_soup = ordered_elements[i + 1][1]
                    paired_elements.append((header_soup, qblock_soup))
                    i += 2
                elif ordered_elements[i][0] == 'qblock' and i + 1 < len(ordered_elements) and ordered_elements[i + 1][0] == 'header':
                    # Found a pair: qblock, header (order might vary)
                    qblock_soup = ordered_elements[i][1]
                    header_soup = ordered_elements[i + 1][1]
                    paired_elements.append((header_soup, qblock_soup))
                    i += 2
                else:
                    # Handle unpaired elements if necessary, or skip
                    print(f"Warning: Unpaired element found at index {i}: {ordered_elements[i][0]}")
                    i += 1

            print(f"Paired {len(paired_elements)} header-qblock sets.")

            processed_blocks_html = []
            assignments_text = []
            downloaded_images = {} # Map original src to local path
            downloaded_files = {} # Map original href to local path

            # Create assets directory for this specific page
            page_assets_dir = run_folder / page_num / "assets"
            page_assets_dir.mkdir(parents=True, exist_ok=True)

            for idx, (header_container, qblock) in enumerate(paired_elements):
                # Create a new soup object to hold the combined content for this specific assignment
                combined_soup = BeautifulSoup('', 'html.parser')
                # Append the qblock first
                combined_soup.append(qblock.extract()) # extract() removes it from original tree

                # --- Process Images (ShowPicture, ShowPictureQ2WH) ---
                # ИСПРАВЛЕНО: Ищем оба типа вызовов, но обрабатываем только те, которые должны создать <img>
                # В оригинальном скрипте `ShowPicture` вызывает `ShowPictureQ2WH`, которая создает <img> внутри <a>
                # Мы будем искать скрипты, вызывающие `ShowPictureQ2WH` или `ShowPicture` (предполагая, что они создают <img>)
                # и заменять их на <img> теги, скачивая изображение.
                # Теперь они могут быть в qblock (внутри combined_soup после добавления).
                for script_tag in combined_soup.find_all('script', string=re.compile(r'ShowPicture\w*\s*\(\s*[\'\"][^\'\"]+[\'\"]', re.IGNORECASE)):
                    script_text = script_tag.get_text()
                    # Попробуем оба паттерна
                    match_q2wh = re.search(r"ShowPictureQ2WH\s*\(\s*['\"]([^'\"]+)['\"]", script_text, re.IGNORECASE)
                    match_gen = re.search(r"ShowPicture\w*\s*\(\s*['\"]([^'\"]+)['\"]", script_text, re.IGNORECASE)

                    img_src = None
                    if match_q2wh:
                        img_src = match_q2wh.group(1)
                        print(f"Found ShowPictureQ2WH call, image src: {img_src}")
                    elif match_gen and not match_q2wh: # Если не Q2WH, но другая функция
                        img_src = match_gen.group(1)
                        print(f"Found ShowPicture call, image src: {img_src}")

                    if img_src:
                        # Download image and get local path
                        local_path = self._download_asset_with_context(page, img_src, page_assets_dir, self.base_url, files_location_prefix, asset_type='image')
                        if local_path:
                            # ИСПРАВЛЕНО: Сохраняем путь ОТНОСИТЕЛЬНО папки страницы (где будет лежать HTML)
                            downloaded_images[img_src] = str(local_path.relative_to(run_folder / page_num)) # Стало: относительно папки страницы
                            # Create new <img> tag with local path RELATIVE TO THE HTML FILE'S DIRECTORY
                            # The HTML file will be saved as run_folder / page_num / f"{page_num}.html"
                            # So, the img src should be e.g. "assets/filename.jpg"
                            img_relative_path_from_html = local_path.relative_to(run_folder / page_num) # Path object
                            new_img = combined_soup.new_tag('img', src=str(img_relative_path_from_html), alt='Downloaded FIPI Image')
                            # Replace the <script> tag with the <img> tag
                            script_tag.replace_with(new_img)
                            print(f"Replaced script with img tag: {new_img}")


                # --- Process Images inside <a> tags (often created by ShowPictureQ2WH) ---
                # Find <img> tags inside <a> tags that might be previews for downloads
                # These often have src="../../docs/.../simg1_...gif" (small preview)
                # The ShowPictureQ2WH function might create the <img> directly inside the <a>
                # We process them *after* handling the scripts above, so the <img> tags exist in soup
                for a_tag in combined_soup.find_all('a'):
                    img_tag = a_tag.find('img')
                    if img_tag:
                        # Get the src of the image, assuming it's relative like the file links
                        img_src = img_tag.get('src')
                        if img_src:
                            # Clean up the src path if it starts with ../../
                            clean_img_src = img_src.lstrip('../../')
                            local_img_path = self._download_asset_with_context(page, clean_img_src, page_assets_dir, self.base_url, files_location_prefix, asset_type='image')
                            if local_img_path:
                                # ИСПРАВЛЕНО: Сохраняем путь ОТНОСИТЕЛЬНО папки страницы
                                downloaded_images[clean_img_src] = str(local_img_path.relative_to(run_folder / page_num)) # Стало
                                # Update the img src to point to the local file RELATIVE TO THE HTML FILE'S DIRECTORY
                                img_relative_path_from_html = local_img_path.relative_to(run_folder / page_num) # Path object
                                img_tag['src'] = str(img_relative_path_from_html)
                                print(f"Updated img src inside <a> to local file: {img_tag['src']}")


                # --- Process Files (e.g., .zip from links) ---
                # Find links that might trigger file downloads via javascript or direct href
                for a_tag in combined_soup.find_all('a'):
                    href = a_tag.get('href')
                    # Извлекаем путь из javascript: ссылки, если необходимо
                    file_path = href
                    if href and href.startswith('javascript:'):
                        # Example: javascript:var wnd=window.open('../../docs/.../file.zip',...
                        match = re.search(r"window\.open\(\s*['\"]([^'\"]+\.zip|[^'\"]+\.rar|[^'\"]+\.pdf|doc|docx|xls|xlsx)['\"]", href, re.I)
                        if match:
                            file_path = match.group(1)
                            # Remove leading ../../ if present, as it's relative to base_url
                            file_path = file_path.lstrip('../../')
                    # Check if file_path is likely a file path
                    if file_path and re.search(r'\.(zip|rar|pdf|doc|docx|xls|xlsx)$', file_path, re.I):
                        # Attempt download
                        local_path = self._download_asset_with_context(page, file_path, page_assets_dir, self.base_url, files_location_prefix, asset_type='file')
                        if local_path:
                            # ИСПРАВЛЕНО: Сохраняем путь ОТНОСИТЕЛЬНО папки страницы
                            downloaded_files[file_path] = str(local_path.relative_to(run_folder / page_num)) # Стало
                            # Update the href in the link to point to the local file RELATIVE TO THE HTML FILE'S DIRECTORY
                            file_relative_path_from_html = local_path.relative_to(run_folder / page_num) # Path object
                            a_tag['href'] = str(file_relative_path_from_html)
                            print(f"Updated link href to local file: {a_tag['href']}")


                # --- Remove duplicate or undefined <img> tags based on attributes ---
                for img_tag in combined_soup.find_all('img'):
                    if img_tag.get('alt') == 'undefined' or img_tag.get('align') or img_tag.get('border'):
                        img_tag.decompose()

                # --- Remove the original answer input field from FIPI HTML ---
                # ИСПРАВЛЕНО: Удаляем поле ввода ответа, которое было на сайте FIPI
                # Теперь ищем внутри combined_soup (всего фрагмента задания)
                for input_tag in combined_soup.find_all('input', attrs={'name': 'answer'}):
                    input_tag.decompose() # Удаляем элемент из дерева BeautifulSoup
                    print(f"Removed original FIPI answer input field: {input_tag}")


                # --- Append the header container (task-header-panel) after the qblock ---
                # Extract the task-header-panel from the header_container
                task_header_panel = header_container.find('div', class_='task-header-panel')
                if task_header_panel:
                    # Modify the onclick attribute to work in the standalone HTML for the info button INSIDE the panel
                    info_button = task_header_panel.find('div', class_='info-button')
                    if info_button:
                         # Modify the onclick attribute to work in the standalone HTML
                        # The original onclick="this.parentNode.classList.toggle("show-info")" might not work as expected
                        # when the HTML is saved separately. We'll add a generic JS function call.
                        # ИСПРАВЛЕНО: Обновляем onclick у кнопки info_button внутри панели
                        info_button['onclick'] = f"toggleInfo(this); return false;" # Add return false to prevent any default action
                        print(f"Found and processed info button for assignment pair {idx}")
                    # Append the task-header-panel to the combined soup
                    combined_soup.append(task_header_panel.extract()) # extract() removes it from header_container)
                    print(f"Appended task-header-panel for assignment pair {idx}")
                else:
                    print(f"Warning: No task-header-panel found in header container for assignment pair {idx}")


                # --- Clean up remaining scripts and MathML ---
                # ИСПРАВЛЕНО: Возвращаем удаление MathML тегов, как в оригинальном скрипте
                # Это позволяет MathJax обрабатывать оставшиеся формулы (LaTeX и т.п.).
                for math_tag in combined_soup.find_all(['math','mml:math']):
                    math_tag.decompose()
                # Удаляем все скрипты, кроме тех, что были обработаны выше.
                # Те, что были обработаны, уже заменены и не находятся тут.
                for s in combined_soup.find_all('script'):
                    # Удаляем все оставшиеся скрипты, которые не были обработаны выше.
                    # Те, что были обработаны, уже заменены и не находятся тут.
                    s.decompose() # Удаляем все оставшиеся скрипты


                processed_html = str(combined_soup)
                processed_blocks_html.append(processed_html)
                assignments_text.append(combined_soup.get_text(separator='\n', strip=True))

            browser.close() # Close browser after scraping

            return {
                "page_name": page_num,
                "url": page_url,
                "assignments": assignments_text,
                "blocks_html": processed_blocks_html, # Теперь содержит объединённый HTML для каждой пары
                "images": downloaded_images,
                "files": downloaded_files
            }

    def _download_asset_with_context(self, page, asset_src: str, save_dir: Path, base_url: str, files_location_prefix: str, asset_type: str = 'image') -> Path:
        """
        Downloads an image or file from the FIPI server and saves it locally using the provided page's request context.

        Args:
            page: The Playwright page object used for making the request.
            asset_src (str): The source path of the asset relative to the server.
            save_dir (Path): The local directory where the asset should be saved.
            base_url (str): The base URL of the FIPI site.
            files_location_prefix (str): Prefix path for files on the server.
            asset_type (str): 'image' or 'file' to determine how to handle the response.

        Returns:
            Path: The Path object to the locally saved asset file if successful,
                  otherwise None.
        """
        # Construct the full URL. The asset_src might already contain the prefix or be relative to it.
        # The files_location_prefix often contains '../..' or similar.
        # We assume asset_src is relative to the files_location_prefix context.
        # So, the full URL is base_url + files_location_prefix + asset_src
        full_asset_path = files_location_prefix + asset_src
        asset_url = urljoin(base_url, full_asset_path)
        print(f"Attempting to download {asset_type}: {asset_url}")
        try:
            # Use the request context of the page, which inherits context settings
            response = page.request.get(asset_url)
            if response.ok:
                # Use the last part of the original path to avoid potential directory traversal
                save_filename = Path(asset_src).name
                save_path = save_dir / save_filename
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(response.body())
                print(f"Successfully downloaded {asset_type} to {save_path}")
                return save_path
            else:
                print(f"Warning: Failed to download {asset_type} {asset_url}. Status: {response.status}")
                return None
        except Exception as e:
            print(f"Error downloading {asset_type} {asset_url}: {e}")
            return None