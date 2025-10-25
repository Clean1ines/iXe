"""
Module for scraping data from the FIPI website.
This module provides the `FIPIScraper` class which handles interactions with the
FIPI website using Playwright to fetch subject listings and assignment pages.
It delegates the actual HTML processing logic to `PageProcessingOrchestrator`.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from playwright.sync_api import sync_playwright
from utils.downloader import AssetDownloader
from processors.page_processor import PageProcessingOrchestrator

# Импорты для зависимостей
from processors.html_data_processors import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover
)
from utils.element_pairer import ElementPairer
from utils.metadata_extractor import MetadataExtractor
from models.problem_builder import ProblemBuilder
from processors.asset_processor_interface import AssetProcessor

logger = logging.getLogger(__name__)


class FIPIScraper:
    """
    A class to scrape assignment data from the FIPI website.

    This class uses Playwright to interact with the website, fetch pages,
    and extract relevant information like subject listings and assignment content.
    It delegates the actual HTML processing logic to `PageProcessingOrchestrator`.
    """

    def __init__(
        self,
        base_url: str,
        subjects_url: str = None,
        user_agent: str = None,
        headless: bool = True,
        # --- НОВЫЕ ЗАВИСИМОСТИ ---
        processors: Optional[List[AssetProcessor]] = None,
        pairer: Optional[ElementPairer] = None,
        extractor: Optional[MetadataExtractor] = None,
        builder: Optional[ProblemBuilder] = None
        # ------------------------
    ):
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
            processors (List[AssetProcessor], optional): List of HTML processors to use.
                                                         If not provided, default processors will be instantiated.
            pairer (ElementPairer, optional): Element pairer instance to use.
                                             If not provided, a default instance will be created.
            extractor (MetadataExtractor, optional): Metadata extractor instance to use.
                                                    If not provided, a default instance will be created.
            builder (ProblemBuilder, optional): Problem builder instance to use.
                                                If not provided, a default instance will be created.
        """
        self.base_url = base_url
        self.subjects_url = subjects_url if subjects_url else base_url
        self.user_agent = user_agent
        self.headless = headless

        # Сохраняем внедрённые зависимости как атрибуты
        self._processors = processors or [
            ImageScriptProcessor(),
            FileLinkProcessor(),
            TaskInfoProcessor(),
            InputFieldRemover(),
            MathMLRemover(),
            UnwantedElementRemover()
        ]
        self._pairer = pairer or ElementPairer()
        self._extractor = extractor or MetadataExtractor()
        self._builder = builder or ProblemBuilder()

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

    def scrape_page(self, proj_id: str, page_num: str, run_folder: Path) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Scrapes a specific page of assignments for a given subject by delegating
        the HTML processing logic to `PageProcessingOrchestrator`.

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
        logger.info(f"Scraping page {page_num} for project {proj_id}, URL: {page_url}")

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

            page_content = page.content()

            # --- Delegate to Orchestrator ---
            logger.debug("Initializing AssetDownloader and PageProcessingOrchestrator...")
            # Create a simple factory that returns the already-instantiated downloader
            downloader = AssetDownloader(page=page, base_url=self.base_url, files_location_prefix=files_location_prefix)

            def asset_downloader_factory(page_obj, base_url, prefix):
                return downloader

            # Создаём PageProcessingOrchestrator, передавая внедрённые зависимости
            orchestrator = PageProcessingOrchestrator(
                asset_downloader_factory=asset_downloader_factory,
                processors=self._processors, # <- Используем внедрённые
                metadata_extractor=self._extractor, # <- Используем внедрённые
                problem_builder=self._builder, # <- Используем внедрённые
                element_pairer=self._pairer # <- Используем внедрённые
            )

            logger.info("Delegating page processing to PageProcessingOrchestrator...")
            problems, scraped_data = orchestrator.process(
                page_content=page_content,
                proj_id=proj_id,
                page_num=page_num,
                run_folder=run_folder,
                base_url=self.base_url,
                files_location_prefix=files_location_prefix,
                page=page, # Pass the page object for AssetDownloader if needed internally
            )
            logger.info("Page processing completed by Orchestrator.")
            # -------------------------------

            browser.close()
        return problems, scraped_data


