"""
Module for scraping FIPI website content and orchestrating the processing pipeline.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.browser_manager import BrowserManager  # Import BrowserManager instead of BrowserPoolManager
from utils.metadata_extractor import MetadataExtractor
from models.problem_builder import ProblemBuilder
from processors.html import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover
)
from processors.page_processor import PageProcessingOrchestrator
from models.problem_schema import Problem
from utils.downloader import AssetDownloader
from utils.task_number_inferer import TaskNumberInferer
from services.specification import SpecificationService
from utils.fipi_urls import FIPI_BASE_URL, FIPI_QUESTIONS_URL, FIPI_SUBJECTS_LIST_URL

logger = logging.getLogger(__name__)


class FIPIScraper:
    """
    Orchestrates the scraping and processing of FIPI website content.
    This class coordinates browser management, page navigation, HTML parsing,
    asset downloading, and transformation into structured Problem instances.
    It relies on dependency injection for components like BrowserManager to
    enable testing and modularity.
    """

    def __init__(
        self,
        base_url: str,
        browser_manager: BrowserManager,  # Accept BrowserManager instead of BrowserPoolManager
        subjects_url: str,
        page_delay: float = 1.0,
        builder: Optional[ProblemBuilder] = None,
        specification_service: Optional[SpecificationService] = None,
        task_inferer: Optional[TaskNumberInferer] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ):
        """
        Initializes the scraper with necessary dependencies and configuration.
        
        Args:
            base_url (str): Base URL of the FIPI questions page.
            browser_manager (BrowserManager): Instance to manage browser context and pages.
            subjects_url (str): URL to fetch the list of subjects/projects.
            page_delay (float): Delay between page operations to avoid detection/blocking.
            builder (ProblemBuilder, optional): Problem builder instance to use.
            specification_service (SpecificationService, optional): Service for official specifications.
            task_inferer (TaskNumberInferer, optional): Component for inferring task numbers.
            max_retries (int): Maximum number of retry attempts for network operations.
            initial_delay (float): Initial delay for retry backoff.
        """
        self.base_url = base_url
        self.browser_manager = browser_manager  # Store BrowserManager instance
        self.subjects_url = subjects_url
        self.page_delay = page_delay
        self.session = requests.Session()
        # Set browser-like headers to avoid blocking
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        })
        self.task_inferer = task_inferer
        self.specification_service = specification_service
        self.max_retries = max_retries
        self.initial_delay = initial_delay

    async def get_projects(self, subjects_list_page) -> Dict[str, str]:
        """
        Parses the subjects list page HTML to extract project ID to subject name mappings.
        NOTE: This method relies on static HTML containing <a> tags with 'proj=' in the href.
        It may not work with dynamically generated subject lists like the current FIPI index.php.
        """
        # Handle if Page object is passed instead of HTML content
        if hasattr(subjects_list_page, 'content') and callable(subjects_list_page.content):
            logger.debug("Detected Page object, extracting HTML content...")
            subjects_list_page_content = await subjects_list_page.content()
            # Heuristic check if the page is likely the new dynamic index.php
            # This is fragile, but better than nothing for a deprecated capability
            # Check for common indicators of the subject list container or specific subject names rendered as divs/spans
            # For now, just warn if proj= is not found in the initial content fetched
            if 'proj=' not in subjects_list_page_content:
                 logger.warning("HTML content fetched from page does not contain 'proj=' in href attributes. "
                                "The page might be dynamically generated (e.g., current FIPI index.php), "
                                "making static parsing with BeautifulSoup ineffective for project discovery.")
        elif isinstance(subjects_list_page, str):
            subjects_list_page_content = subjects_list_page
        else:
            logger.warning("Unexpected input type for subjects_list_page. Attempting string conversion.")
            subjects_list_page_content = str(subjects_list_page)

        logger.info("Extracting projects from subjects list page using BeautifulSoup...")
        logger.debug(f"Raw HTML content (first 500 chars): {subjects_list_page_content[:500]}")
        soup = BeautifulSoup(subjects_list_page_content, 'html.parser')
        projects = {}

        # Look for links with 'proj=' in the href attribute
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)

            # Check if the link contains 'proj=' and has text content
            if 'proj=' in href and text:
                # Extract proj_id from URL
                parsed_url = urlparse(href)
                query_params = parsed_url.query.split('&')
                proj_param = None

                for param in query_params:
                    if param.startswith('proj='):
                        proj_param = param.split('=')[1]
                        break
                # Fallback: try to find proj in the href string directly
                if not proj_param and 'proj=' in href:
                    parts = href.split('proj=')
                    if len(parts) > 1:
                        proj_param = parts[1].split('&')[0].split('#')[0]

                if proj_param:
                    # Clean subject name - remove extra spaces and non-printable characters
                    clean_name = ' '.join(text.split())
                    projects[proj_param] = clean_name
                    logger.debug(f"Found project: {proj_param} -> {clean_name}")

        logger.info(f"Successfully found {len(projects)} projects")
        logger.debug(f"Complete projects mapping: {projects}")
        return projects

    async def scrape_page(
        self,
        proj_id: str,
        page_num: str,
        run_folder: Path,
        subject: str,
    ) -> Tuple[List[Problem], Dict[str, Any]]:
        """
        Scrapes a single page of problems for a given project ID.
        
        Args:
            proj_id (str): Project ID for the subject.
            page_num (str): Page number to scrape (e.g., "1", "init").
            run_folder (Path): Directory to store downloaded assets and outputs.
            subject (str): Subject name for context (e.g., "math").
        
        Returns:
            Tuple[List[Problem], Dict[str, Any]]: List of structured Problem objects
            and additional scraped metadata.
        """
        logger.info(f"Scraping page {page_num} for project {proj_id} (subject: {subject})...")
        
        # CORRECT URL CONSTRUCTION for FIPI bank
        # Base URL should be questions.php endpoint
        base_questions_url = FIPI_QUESTIONS_URL
        full_url = f"{base_questions_url}?proj={proj_id}&page={page_num}"
        logger.debug(f"Navigating to URL: {full_url}")
        
        # Get a *general* page instance from the browser manager (not tied to a specific subject)
        page = await self.browser_manager.get_general_page()
        
        for attempt in range(self.max_retries):
            try:
                # Navigate to the specific questions page
                await page.goto(full_url, wait_until="networkidle", timeout=30000)
                
                # Wait for content to load
                logger.debug("Waiting for .qblock elements to appear...")
                await page.wait_for_selector(".qblock", timeout=60000)  # Increased timeout
                
                # Get page content
                page_content = await page.content()
                logger.debug(f"Page content length: {len(page_content)} characters")
                
                # Create asset downloader factory that uses the same page context
                def asset_downloader_factory(page_obj, base, prefix):
                    return AssetDownloader(page=page_obj)
                
                # Create the processing orchestrator
                orchestrator = PageProcessingOrchestrator(
                    asset_downloader_factory=asset_downloader_factory,
                    processors=[
                        ImageScriptProcessor(),
                        FileLinkProcessor(),
                        TaskInfoProcessor(),
                        InputFieldRemover(),
                        MathMLRemover(),
                        UnwantedElementRemover()
                    ],
                    metadata_extractor=MetadataExtractor(),
                    problem_builder=ProblemBuilder(),
                    task_inferer=self.task_inferer,
                    specification_service=self.specification_service,  # Pass specification service
                )
                
                # Process the page content
                logger.debug("Starting page processing orchestrator...")
                problems, scraped_data = await orchestrator.process(
                    page_content=page_content,
                    proj_id=proj_id,
                    page_num=page_num,
                    run_folder=run_folder,
                    base_url=base_questions_url,  # Pass the correct base URL
                    subject=subject,
                    page=page # Pass the page object to the orchestrator
                )
                
                logger.info(f"Successfully scraped {len(problems)} problems from page {page_num}")
                return problems, scraped_data
                
            except (PlaywrightTimeoutError, Exception) as e:
                logger.warning(f"Attempt {attempt + 1} failed for page {page_num} (proj_id: {proj_id}): {e}")
                
                if attempt < self.max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = self.initial_delay * (2 ** attempt)
                    logger.debug(f"Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for page {page_num} (proj_id: {proj_id})")
                    raise
            finally:
                # Close the general page after scraping
                await page.close()

    async def close(self):
        """Closes the associated browser resources."""
        await self.browser_manager.close()
