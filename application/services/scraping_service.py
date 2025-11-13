"""
Application service for scraping operations.

This service coordinates the scraping process, handling the interaction
between domain entities and infrastructure adapters.
"""
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from domain.models.problem import Problem
from domain.interfaces.external_services import (
    IBrowserService,
    IDatabaseService,
    ISpecificationService
)
from domain.value_objects.scraping.subject_info import SubjectInfo
from domain.value_objects.scraping.scraping_config import ScrapingConfig
from infrastructure.adapters.html_element_pairer_adapter import HTMLElementPairerAdapter
from infrastructure.adapters.fipi_html_metadata_extractor import FIPIHTMLMetadataExtractor
from infrastructure.adapters.task_classifier_adapter import TaskClassifierAdapter
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService

logger = logging.getLogger(__name__)

class ScrapingService:
    """
    Application service for scraping operations.
    
    Business Rules:
    - Coordinates the scraping workflow
    - Handles pagination logic
    - Manages file storage and database operations
    - Provides progress reporting
    - Handles error recovery and retries
    """
    
    def __init__(
        self,
        browser_service: IBrowserService,
        database_service: IDatabaseService,
        specification_service: ISpecificationService,
        element_pairer: HTMLElementPairerAdapter,
        metadata_extractor: FIPIHTMLMetadataExtractor,
        task_classifier: TaskClassifierAdapter,
        answer_type_service: AnswerTypeService,
        metadata_enhancer: MetadataExtractionService
    ):
        """
        Initialize scraping service with dependencies.
        
        Args:
            browser_service: Service for browser management
            database_service: Service for database operations
            specification_service: Service for exam specifications
            element_pairer: Adapter for pairing HTML elements
            metadata_extractor: Adapter for extracting metadata
            task_classifier: Adapter for classifying tasks
            answer_type_service: Service for detecting answer types
            metadata_enhancer: Service for enhancing metadata
        """
        self.browser_service = browser_service
        self.database_service = database_service
        self.specification_service = specification_service
        self.element_pairer = element_pairer
        self.metadata_extractor = metadata_extractor
        self.task_classifier = task_classifier
        self.answer_type_service = answer_type_service
        self.metadata_enhancer = metadata_enhancer
    
    async def scrape_subject(
        self,
        subject_info: SubjectInfo,
        config: ScrapingConfig
    ) -> Dict[str, Any]:
        """
        Scrape all pages for a subject.
        
        Args:
            subject_info: Subject information
            config: Scraping configuration
            
        Returns:
            Dictionary with scraping results
        """
        logger.info(f"Starting scraping for subject: {subject_info.official_name}")
        
        # Setup directories
        output_dir = subject_info.output_directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get browser instance
        browser = await self.browser_service.get_browser()
        
        try:
            results = {
                "subject": subject_info.official_name,
                "total_pages": 0,
                "total_problems": 0,
                "success": True,
                "errors": [],
                "page_results": []
            }
            
            # Scrape initial page
            init_result = await self._scrape_page(
                browser=browser,
                proj_id=subject_info.proj_id,
                page_num="init",
                output_dir=output_dir,
                subject_key=subject_info.subject_key,
                config=config
            )
            
            results["page_results"].append(init_result)
            results["total_pages"] += 1
            results["total_problems"] += len(init_result.get("problems", []))
            
            if not init_result.get("success", False):
                results["success"] = False
                results["errors"].append(init_result.get("error", "Unknown error on init page"))
            
            # Determine last page number
            last_page_num = await self._get_last_page_number(browser, subject_info.proj_id)
            
            # Scrape numbered pages
            page_num = 1
            empty_count = 0
            
            while True:
                # Check if we've reached the last page
                if last_page_num is not None and page_num > last_page_num:
                    logger.info(f"Reached last page {last_page_num}")
                    break
                
                # Check if we've hit max empty pages
                if empty_count >= config.max_empty_pages:
                    logger.info(f"Reached {config.max_empty_pages} consecutive empty pages")
                    break
                
                # Scrape current page
                page_result = await self._scrape_page(
                    browser=browser,
                    proj_id=subject_info.proj_id,
                    page_num=str(page_num),
                    output_dir=output_dir,
                    subject_key=subject_info.subject_key,
                    config=config
                )
                
                results["page_results"].append(page_result)
                results["total_pages"] += 1
                
                if page_result.get("success", False):
                    page_problems = len(page_result.get("problems", []))
                    results["total_problems"] += page_problems
                    
                    if page_problems == 0:
                        empty_count += 1
                    else:
                        empty_count = 0
                else:
                    results["success"] = False
                    results["errors"].append(
                        f"Page {page_num} failed: {page_result.get('error', 'Unknown error')}"
                    )
                
                page_num += 1
            
            return results
            
        finally:
            # Always release browser
            await self.browser_service.release_browser(browser)
    
    async def _scrape_page(
        self,
        browser: Any,
        proj_id: str,
        page_num: str,
        output_dir: Path,
        subject_key: str,
        config: ScrapingConfig
    ) -> Dict[str, Any]:
        """
        Scrape a single page.
        
        Args:
            browser: Browser instance
            proj_id: Project ID
            page_num: Page number
            output_dir: Output directory
            subject_key: Subject key
            config: Scraping configuration
            
        Returns:
            Dictionary with page scraping results
        """
        from infrastructure.adapters.database_adapter import config as app_config
        
        try:
            logger.debug(f"Scraping page {page_num} for proj_id {proj_id}")
            
            # Construct URL
            base_url = app_config.FIPI_QUESTIONS_URL
            url = f"{base_url}?proj={proj_id}"
            if page_num != "init":
                url += f"&page={page_num}"
            
            # Get page content
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=config.timeout_seconds * 1000)
            
            # Save raw HTML
            raw_html = await page.content()
            raw_html_path = output_dir / "raw_html" / f"page_{page_num}.html"
            raw_html_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(raw_html_path, "w", encoding="utf-8") as f:
                f.write(raw_html)
            
            # Extract problems from HTML
            problems_data = await self._extract_problems_from_html(
                html_content=raw_html,
                page_num=page_num,
                subject_key=subject_key,
                config=config
            )
            
            # Process problems
            problems = []
            for problem_data in problems_data:
                try:
                    # Create domain problem (implementation would use ProblemFactory)
                    # This is a placeholder - actual implementation would use the factory
                    problems.append(problem_data)
                except Exception as e:
                    logger.error(f"Failed to process problem: {e}")
            
            # Save to database
            for problem in problems:
                try:
                    # Save problem to database (implementation would use database service)
                    pass
                except Exception as e:
                    logger.error(f"Failed to save problem: {e}")
            
            return {
                "page_num": page_num,
                "success": True,
                "problems": problems,
                "raw_html_path": str(raw_html_path),
                "url": url,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}", exc_info=True)
            return {
                "page_num": page_num,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            try:
                await page.close()
            except:
                pass
    
    async def _extract_problems_from_html(
        self,
        html_content: str,
        page_num: str,
        subject_key: str,
        config: ScrapingConfig
    ) -> List[Dict[str, Any]]:
        """
        Extract problems from HTML content.
        
        Args:
            html_content: HTML content to extract from
            page_num: Page number
            subject_key: Subject key
            config: Scraping configuration
            
        Returns:
            List of extracted problem data
        """
        # This would use the element pairer, metadata extractor, etc.
        # Placeholder implementation
        return []
    
    async def _get_last_page_number(self, browser: Any, proj_id: str) -> Optional[int]:
        """
        Get the last page number from the pager.
        
        Args:
            browser: Browser instance
            proj_id: Project ID
            
        Returns:
            Last page number or None if not found
        """
        from infrastructure.adapters.database_adapter import config as app_config
        
        try:
            page = await browser.new_page()
            url = f"{app_config.FIPI_QUESTIONS_URL}?proj={proj_id}&page=1"
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_selector(".pager", timeout=10000)
            
            # Get last page number from pager
            last_page_text = await page.evaluate("""
                () => {
                    const pager = document.querySelector('.pager');
                    if (!pager) return null;
                    const buttons = Array.from(pager.querySelectorAll('.button'));
                    if (buttons.length === 0) return null;
                    const lastButton = buttons[buttons.length - 1];
                    return lastButton.getAttribute('p');
                }
            """)
            
            if last_page_text and last_page_text.isdigit():
                return int(last_page_text)
            return None
            
        except Exception as e:
            logger.warning(f"Could not determine last page number: {e}")
            return None
        finally:
            try:
                await page.close()
            except:
                pass
