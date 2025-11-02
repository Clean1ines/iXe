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
from playwright.async_api import Page
from utils.browser_manager import BrowserManager
from utils.metadata_extractor import MetadataExtractor
from models.problem_builder import ProblemBuilder
from processors.html_data_processors import (
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

# Constants for FIPI URLs - CORRECTED BASE URL
FIPI_BASE_URL = "https://ege.fipi.ru"
FIPI_QUESTIONS_URL = f"{FIPI_BASE_URL}/bank/questions.php"
FIPI_SUBJECTS_URL = f"{FIPI_BASE_URL}/bank"

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
        browser_manager: BrowserManager,
        subjects_url: str,
        page_delay: float = 1.0,
        builder: Optional[ProblemBuilder] = None,
        specification_service: Optional[SpecificationService] = None,
        task_inferer: Optional[TaskNumberInferer] = None,
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
        """
        self.base_url = base_url
        self.browser_manager = browser_manager
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

    async def get_projects(self, subjects_list_page: str) -> Dict[str, str]:
        """
        Parses the subjects list page HTML to extract project ID to subject name mappings.
        
        Args:
            subjects_list_page (str): HTML content of the subjects listing page.
        
        Returns:
            Dict[str, str]: Mapping of project IDs to their human-readable subject names.
        """
        logger.info("Extracting projects from subjects list page...")
        logger.debug(f"Raw HTML content (first 500 chars): {subjects_list_page[:500]}")
        soup = BeautifulSoup(subjects_list_page, 'html.parser')
        projects = {}
        
        # Updated logic to find subject links on the correct FIPI page structure
        # Look for elements that contain subject information
        for element in soup.select('[href*="questions.php?proj="], [href*="&proj="], .subject-item, .subject-name'):
            href = element.get('href', '')
            text = element.get_text(strip=True)
            
            if not href or not text:
                continue
                
            # Parse project ID from URL
            parsed_url = urlparse(href)
            query_params = parsed_url.query.split('&')
            proj_id = None
            
            for param in query_params:
                if param.startswith('proj='):
                    proj_id = param.split('=')[1]
                    break
            
            # Fallback: try to find proj in the href string
            if not proj_id and 'proj=' in href:
                parts = href.split('proj=')
                if len(parts) > 1:
                    proj_id = parts[1].split('&')[0].split('#')[0]
            
            if proj_id and text:
                # Clean subject name - remove extra spaces and non-printable characters
                clean_name = ' '.join(text.split())
                projects[proj_id] = clean_name
                logger.debug(f"Found project: {proj_id} -> {clean_name}")
        
        # If we didn't find any projects with the above selectors, try a more generic approach
        if not projects:
            logger.warning("No projects found with primary selectors, trying fallback method...")
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                if "proj=" in href and text:
                    # Extract proj_id from URL
                    if "proj=" in href:
                        proj_id = href.split("proj=")[-1].split("&")[0].split("#")[0]
                        clean_name = ' '.join(text.split())
                        projects[proj_id] = clean_name
                        logger.debug(f"Found project (fallback): {proj_id} -> {clean_name}")
        
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
        base_questions_url = f"{FIPI_BASE_URL}/bank/questions.php"
        full_url = f"{base_questions_url}?proj={proj_id}&page={page_num}"
        logger.debug(f"Navigating to URL: {full_url}")
        
        # Get a page instance from the browser manager
        page = await self.browser_manager.get_page(full_url)
        
        try:
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
                subject=subject
            )
            
            logger.info(f"Successfully scraped {len(problems)} problems from page {page_num}")
            return problems, scraped_data
            
        except Exception as e:
            logger.exception("Exception occurred during page scraping:")
            logger.error(f"Error scraping page {page_num} for project {proj_id}: {e}", exc_info=True)
            raise
        finally:
            # Return the page to the browser manager pool
            await self.browser_manager.return_page(page)

    async def close(self):
        """Closes the associated browser resources."""
        await self.browser_manager.close()
