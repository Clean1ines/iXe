"""
Application service for scraping a single page of problems.
Implements the use case: ScrapePageForSubject
"""
from typing import List, Tuple, Dict, Any
from pathlib import Path
from domain.interfaces.html_processor import IHTMLProcessor
from domain.interfaces.infrastructure_adapters import IDatabaseProvider
from domain.models.problem_schema import Problem
from utils.fipi_urls import FIPI_QUESTIONS_URL
from datetime import datetime
import logging
import asyncio
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


logger = logging.getLogger(__name__)


class PageScrapingService:
    def __init__(
        self,
        html_processor: IHTMLProcessor,
        problem_repo: IDatabaseProvider,
        browser_manager,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ):
        self._html_processor = html_processor
        self._problem_repo = problem_repo  # This is IDatabaseProvider which already acts as repository
        self._browser_manager = browser_manager
        self._max_retries = max_retries
        self._initial_delay = initial_delay

    async def scrape_page(
        self,
        proj_id: str,
        page_num: str,
        run_folder: Path,
        subject: str,
    ) -> Tuple[List[Problem], Dict[str, Any]]:
        """
        Application use case: scrape a single page of problems.
        
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
        
        # Construct URL
        base_questions_url = FIPI_QUESTIONS_URL
        full_url = f"{base_questions_url}?proj={proj_id}&page={page_num}"
        logger.debug(f"Navigating to URL: {full_url}")
        
        # Get browser page with retry logic
        page = await self._get_page_with_retry(full_url)
        
        try:
            # Get page content
            page_content = await page.content()
            logger.debug(f"Page content length: {len(page_content)} characters")
            
            # Create asset downloader factory that uses the same page context
            def asset_downloader_factory(page_obj, base, prefix):
                from utils.downloader import AssetDownloader
                return AssetDownloader(page=page_obj)
            
            # Process the page content using the existing orchestrator
            run_folder_page = run_folder / page_num
            
            from processors.page_processor import PageProcessingOrchestrator
            orchestrator = PageProcessingOrchestrator(html_processor=self._html_processor)
            
            results = await orchestrator.process_page(
                page_content=page_content,
                subject=subject,
                base_url=base_questions_url,
                run_folder_page=run_folder_page,
                downloader=asset_downloader_factory(page, base_questions_url, f"../../"),
                files_location_prefix="../../"
            )
            
            # Convert results to Problem objects and save
            problems = []
            for result in results:
                problem = self._create_problem_from_result(result, subject)
                # Use save_problem method from IDatabaseProvider
                self._problem_repo.save_problem(problem)
                problems.append(problem)

            scraped_data = {
                "page_name": page_num,
                "url": full_url,
                "results": results
            }
            
            logger.info(f"Successfully scraped {len(problems)} problems from page {page_num}")
            return problems, scraped_data
            
        finally:
            # Close the page
            await page.close()
    
    async def _get_page_with_retry(self, url: str) -> Page:
        """Get a page with retry logic for network errors."""
        for attempt in range(self._max_retries):
            try:
                page = await self._browser_manager.get_general_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_selector(".qblock", timeout=60000)
                return page
            except (PlaywrightTimeoutError, Exception) as e:
                logger.warning(f"Attempt {attempt + 1} failed for URL {url}: {e}")
                
                if attempt < self._max_retries - 1:
                    delay = self._initial_delay * (2 ** attempt)
                    logger.debug(f"Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self._max_retries} attempts failed for URL {url}")
                    raise

    def _create_problem_from_result(self, result: Dict[str, Any], subject: str) -> Problem:
        """Create Problem instance from processing result."""
        return Problem(
            problem_id=result.get('problem_id', f"{subject}_unknown_{len([])}"),  # len([]) is placeholder
            subject=result.get('subject', subject),
            type=result.get('type', 'unknown'),
            text=result.get('text', ''),
            difficulty_level=result.get('difficulty_level', 'basic'),
            exam_part=result.get('exam_part', 'Part 1'),
            max_score=result.get('max_score', 1),
            created_at=result.get('created_at', datetime.now()),
            # Optional fields with defaults
            answer=result.get('answer'),
            options=result.get('options'),
            solutions=result.get('solutions'),
            kes_codes=result.get('kes_codes', []),
            skills=result.get('skills'),
            task_number=result.get('task_number', 0),
            kos_codes=result.get('kos_codes', []),
            form_id=result.get('form_id'),
            source_url=result.get('source_url'),
            raw_html_path=result.get('raw_html_path'),
            updated_at=result.get('updated_at'),
            metadata=result.get('metadata')
        )
