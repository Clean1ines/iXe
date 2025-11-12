"""
Module for scraping FIPI website content and orchestrating the processing pipeline.
Refactored to follow Clean Architecture principles by delegating to application services.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from resource_management.browser_pool_manager import BrowserPoolManager
from infrastructure.adapters.fipi_html_metadata_extractor import MetadataExtractor
from domain.models.problem_builder import ProblemBuilder
from domain.models.problem_schema import Problem
from infrastructure.adapters.task_number_inferer_adapter import TaskNumberInfererAdapter
from infrastructure.adapters.specification_adapter import SpecificationAdapter
from infrastructure.adapters.block_processor_adapter import BlockProcessorAdapter
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService
from utils.fipi_urls import FIPI_BASE_URL, FIPI_QUESTIONS_URL, FIPI_SUBJECTS_LIST_URL
from infrastructure.adapters.database_adapter import DatabaseAdapter
from infrastructure.adapters.task_classifier_adapter import TaskClassifierAdapter
from datetime import datetime
from application.services.page_scraping_service import PageScrapingService


logger = logging.getLogger(__name__)


class FIPIScraper:
    """
    Orchestrates the scraping and processing of FIPI website content.
    This class now delegates the core scraping logic to application services
    following Clean Architecture principles, while maintaining its role as
    a coordinator for the overall scraping workflow.
    """

    def __init__(
        self,
        base_url: str,
        browser_manager: BrowserPoolManager,
        subjects_url: str,
        spec_service: Optional[SpecificationAdapter] = None,
        task_inferer: Optional[TaskNumberInfererAdapter] = None,
        page_delay: float = 1.0,
        builder: Optional[ProblemBuilder] = None,
        db_manager: Optional[DatabaseAdapter] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ):
        """
        Initializes the scraper with necessary dependencies and configuration.
        
        Args:
            base_url (str): Base URL of the FIPI questions page.
            browser_manager (BrowserPoolManager): Instance to manage browser context and pages.
            subjects_url (str): URL to fetch the list of subjects/projects.
            spec_service (SpecificationAdapter, optional): Service for official specifications.
            task_inferer (TaskNumberInfererAdapter, optional): Component for inferring task numbers.
            page_delay (float): Delay between page operations to avoid detection/blocking.
            builder (ProblemBuilder, optional): Problem builder instance to use.
            db_manager (DatabaseAdapter, optional): Database manager for storing problems.
            max_retries (int): Maximum number of retry attempts for network operations.
            initial_delay (float): Initial delay for retry backoff.
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
        self.db_manager = db_manager
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        
        # Initialize specification service if not provided
        self.spec_service = spec_service
        
        # Initialize task inferer if not provided
        if self.spec_service is not None:
            self.task_inferer = task_inferer or TaskNumberInfererAdapter(self.spec_service)
        else:
            self.task_inferer = task_inferer or TaskNumberInfererAdapter(SpecificationAdapter(Path("data/specs/ege_2026_math_spec.json"), Path("data/specs/ege_2026_math_kes_kos.json")))
        
        # Initialize task classifier
        self.task_classifier = TaskClassifierAdapter(self.task_inferer)
        
        # Initialize the HTML processor (BlockProcessorAdapter implements IHTMLProcessor)
        self.block_processor = BlockProcessorAdapter(
            task_inferer=self.task_inferer,
            task_classifier=self.task_classifier,
            answer_type_service=AnswerTypeService(),
            metadata_enhancer=MetadataExtractionService(
                self.spec_service
            ),
            spec_service=self.spec_service
        )

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
        Delegates the actual scraping to PageScrapingService.
        
        Args:
            proj_id (str): Project ID for the subject.
            page_num (str): Page number to scrape (e.g., "1", "init").
            run_folder (Path): Directory to store downloaded assets and outputs.
            subject (str): Subject name for context (e.g., "math").
        
        Returns:
            Tuple[List[Problem], Dict[str, Any]]: List of structured Problem objects
            and additional scraped metadata.
        """
        # Create the application service that handles the page scraping
        scraping_service = PageScrapingService(
            html_processor=self.block_processor,
            problem_repo=self.db_manager,  # Pass the database manager as the repository
            browser_manager=self.browser_manager,
            max_retries=self.max_retries,
            initial_delay=self.initial_delay
        )
        
        # Delegate the actual scraping to the application service
        return await scraping_service.scrape_page(proj_id, page_num, run_folder, subject)

    async def close(self):
        """Closes the associated browser resources."""
        await self.browser_manager.close()
