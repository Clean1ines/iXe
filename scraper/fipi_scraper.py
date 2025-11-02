"""
Module for scraping data from the FIPI website.
This module provides the `FIPIScraper` class which handles interactions with the
FIPI website using Playwright, managed by BrowserManager, to fetch subject listings and assignment pages.
It delegates the actual HTML processing logic to `PageProcessingOrchestrator`.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from playwright.async_api import Page
from utils.downloader import AssetDownloader
from processors.page_processor import PageProcessingOrchestrator
from utils.browser_manager import BrowserManager
import re

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

    This class uses Playwright, managed by BrowserManager, to interact with the website, fetch pages,
    and extract relevant information like subject listings and assignment content.
    It delegates the actual HTML processing logic to `PageProcessingOrchestrator`.
    """

    def __init__(
        self,
        base_url: str,
        browser_manager: BrowserManager, # NEW DEPENDENCY
        subjects_url: str = None,
        user_agent: str = None,
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
            base_url (str): The base URL for the FIPI site (e.g., https://ege.fipi.ru).
            browser_manager (BrowserManager): Instance of BrowserManager for page acquisition.
            subjects_url (str, optional): The URL for the subjects listing page.
                                          If not provided, defaults to base_url + /bank/.
            user_agent (str, optional): User agent string for the browser session.
                                        Defaults to None, which uses the system default or a predefined one.
            processors (List[AssetProcessor], optional): List of HTML processors to use.
                                                         If not provided, default processors will be instantiated.
            pairer (ElementPairer, optional): Element pairer instance to use.
                                             If not provided, a default instance will be created.
            extractor (MetadataExtractor, optional): Metadata extractor instance to use.
                                                    If not provided, a default instance will be created.
            builder (ProblemBuilder, optional): Problem builder instance to use.
                                                If not provided, a default instance will be created.
        """
        self.base_url = base_url.rstrip("/") # Ensure no trailing slash
        self.browser_manager = browser_manager # STORE THE DEPENDENCY
        # Use provided subjects_url or construct it from base_url
        self.subjects_url = subjects_url if subjects_url else f"{self.base_url}/bank/"
        self.user_agent = user_agent

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

    async def get_projects(self, page: Page) -> Dict[str, str]:
        """
        Fetches the list of available subjects and their project IDs from the FIPI website.

        This method uses the provided page (expected to be on subjects_url) to find the list
        of subjects (typically within a <ul> element with an ID like 'pgp_...'),
        parses the list items (<li>), and extracts the project ID (often from an 'id' attribute like 'p_...')
        and the subject name.

        Args:
            page (Page): Playwright Page instance already navigated to the subjects listing page.

        Returns:
            Dict[str, str]: A dictionary mapping project IDs (str) to subject names (str).
                            Example: {'AC437B...': 'Математика. Профильный уровень', ...}
                            Returns an empty dict if the list is not found or parsing fails.
        """
        logger.info(f"[Fetching subjects] Parsing subjects list from current page: {page.url}")
        # No need to navigate, assume page is already at the correct URL
        projects = {}
        try:
            list_selector = "ul[id^='pgp_']"
            list_element = page.locator(list_selector).first
            if await list_element.count() > 0:
                list_items = list_element.locator("li[id^='p_']")
                count = await list_items.count()
                for i in range(count):
                    item = list_items.nth(i)
                    item_id = await item.get_attribute("id")
                    if item_id and item_id.startswith("p_"):
                        proj_id = item_id[2:]
                    else:
                        logger.warning(f"Skipping item with unexpected ID format: {item_id}")
                        continue
                    subject_name = (await item.inner_text()).strip()
                    if proj_id and subject_name:
                        projects[proj_id] = subject_name
                    else:
                        logger.warning(f"Skipping item with empty ID or name: {item_id}, Name: '{subject_name}'")
        except Exception as e:
            logger.error(f"Error parsing projects list: {e}")
        logger.info(f"[Fetched subjects] Found {len(projects)} subjects.")
        return projects

    async def get_total_pages(self, proj_id: str, subject: str) -> int:
        """Extract total pages from pagination links on the 'init' page."""
        page = await self.browser_manager.get_page(subject)
        # Construct the init URL using the base_url and /bank/index.php
        init_url = f"{self.base_url}/bank/index.php?proj={proj_id}&page=init"
        await page.goto(init_url, wait_until="networkidle")

        max_page = 1
        try:
            # Ищем все ссылки с page= в href
            page_links = page.locator("a[href*='page=']")
            count = await page_links.count()
            for i in range(count):
                link = page_links.nth(i)
                href = await link.get_attribute("href")
                if href:
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        page_num = int(match.group(1))
                        if page_num > max_page:
                            max_page = page_num
        except Exception as e:
            logger.warning(f"Failed to parse pagination: {e}")

        logger.info(f"🔢 Detected {max_page} pages for project {proj_id}")
        return max_page

    async def scrape_page(
        self,
        proj_id: str,
        page_num: str,
        run_folder: Path,
        subject: str # NEW PARAMETER: subject to get the correct page
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Scrapes a specific page of assignments for a given subject by delegating
        the HTML processing logic to `PageProcessingOrchestrator`.

        Args:
            proj_id (str): The project ID corresponding to the subject.
            page_num (str): The page number to scrape (e.g., 'init', '1', '2').
            run_folder (Path): The base run folder where assets should be saved.
            subject (str): The subject name to get the page for via BrowserManager.

        Returns:
            Tuple[List[Problem], Dict[str, Any]]: A tuple containing:
                - A list of Problem objects created from the scraped data.
                - A dictionary with the old scraped data structure (page_name, blocks_html, etc.).
        """
        page = await self.browser_manager.get_page(subject) # GET PAGE FROM BROWSER MANAGER
        # Construct the URL using the base_url and /bank/index.php
        page_url = f"{self.base_url}/bank/index.php?proj={proj_id}&page={page_num}"
        logger.info(f"Scraping page {page_num} for project {proj_id} (subject: {subject}), URL: {page_url}")

        await page.goto(page_url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        logger.info("Page loaded and waited for 3 seconds.")

        try:
            files_location_prefix = await page.evaluate("window.files_location || '../../'")
            logger.info(f"files_location_prefix determined as: {files_location_prefix}")
        except Exception as e:
            logger.warning(f"Could not get files_location from page {page_url}, using default. Error: {e}")
            files_location_prefix = '../../'

        page_content = await page.content()
        logger.info(f"Page content fetched, length: {len(page_content)}")

        # --- Delegate to Orchestrator ---
        logger.debug("Initializing AssetDownloader and PageProcessingOrchestrator...")
        # Create AssetDownloader with only 'page'
        downloader = AssetDownloader(page=page)

        def asset_downloader_factory(page_obj, base_url, prefix):
            # The factory now uses the page provided by the scraper, which comes from BrowserManager
            logger.debug("AssetDownloader factory called.")
            # Return an AssetDownloader instance with the correct page
            return AssetDownloader(page=page_obj)

        # Create PageProcessingOrchestrator without element_pairer
        orchestrator = PageProcessingOrchestrator(
            asset_downloader_factory=asset_downloader_factory,
            processors=self._processors,
            metadata_extractor=self._extractor,
            problem_builder=self._builder,
            # element_pairer=self._pairer # <-- REMOVED from __init__
        )

        logger.info("Delegating page processing to PageProcessingOrchestrator...")
        try:
            # OLD: problems, scraped_data = await orchestrator.process(...)
            # OLD: element_pairer=self._pairer # <-- This caused the error in .process()
            # NEW: Pass element_pairer to the process method if needed - NO, REMOVED
            problems, scraped_data = await orchestrator.process(
                page_content=page_content,
                proj_id=proj_id,
                page_num=page_num,
                run_folder=run_folder,
                base_url=self.base_url,
                files_location_prefix=files_location_prefix,
                page=page, # Pass the page obtained from BrowserManager
                # element_pairer=self._pairer # <-- REMOVED from .process() call
            )
            logger.info("Page processing completed by Orchestrator.")
        except Exception as e:
            logger.error(f"Error in PageProcessingOrchestrator.process: {e}", exc_info=True)
            raise # Re-raise to be caught by the outer except
        # -------------------------------

        return problems, scraped_data

