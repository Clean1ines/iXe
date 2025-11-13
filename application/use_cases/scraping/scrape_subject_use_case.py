"""
Use case for scraping a single subject.

This use case coordinates the scraping process for a single subject,
handling all the business logic while delegating infrastructure concerns
to appropriate adapters.
"""
import logging
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from domain.interfaces.external_services import (
    IBrowserService,
    IDatabaseService,
    ISpecificationService
)
from domain.value_objects.scraping.subject_info import SubjectInfo
from domain.value_objects.scraping.scraping_config import ScrapingConfig
from domain.value_objects.scraping.scraping_result import (
    ScrapingSubjectResult,
    ScrapingPageResult
)
from application.services.page_scraping_service import PageScrapingService
from application.factories.problem_factory import ProblemFactory
from domain.models.problem import Problem

logger = logging.getLogger(__name__)

class ScrapeSubjectUseCase:
    """
    Use case for scraping a single subject.
    
    Business Rules:
    - Handles both initial scraping and updates
    - Manages resource cleanup properly
    - Provides progress reporting
    - Handles errors gracefully
    - Respects scraping configuration
    - Ensures data integrity
    """
    
    def __init__(
        self,
        browser_service: IBrowserService,
        database_service: IDatabaseService,
        specification_service: ISpecificationService,
        page_scraping_service: PageScrapingService,
        problem_factory: ProblemFactory
    ):
        """
        Initialize use case with required dependencies.
        
        Args:
            browser_service: Service for browser management
            database_service: Service for database operations
            specification_service: Service for exam specifications
            page_scraping_service: Service for page scraping
            problem_factory: Factory for creating domain problems
        """
        self.browser_service = browser_service
        self.database_service = database_service
        self.specification_service = specification_service
        self.page_scraping_service = page_scraping_service
        self.problem_factory = problem_factory
    
    async def execute(
        self,
        subject_info: SubjectInfo,
        config: ScrapingConfig
    ) -> ScrapingSubjectResult:
        """
        Execute the scraping use case.
        
        Args:
            subject_info: Subject information for scraping
            config: Scraping configuration
            
        Returns:
            ScrapingSubjectResult containing detailed results
            
        Business Rules:
        - Checks existing data before scraping
        - Initializes database if needed
        - Handles force restart option
        - Provides detailed progress reporting
        - Ensures proper resource cleanup
        """
        logger.info(f"Starting scraping for subject: {subject_info.official_name}")
        start_time = datetime.now()
        page_results: List[ScrapingPageResult] = []
        errors: List[str] = []
        total_problems_found = 0
        total_problems_saved = 0
        
        try:
            # Setup directories
            subject_info.output_directory.mkdir(parents=True, exist_ok=True)
            subject_info.raw_html_directory.mkdir(parents=True, exist_ok=True)
            
            # Handle force restart
            if config.force_restart and subject_info.database_path.exists():
                logger.info(f"Force restart enabled. Deleting existing data for {subject_info.official_name}")
                shutil.rmtree(subject_info.output_directory, ignore_errors=True)
                subject_info.output_directory.mkdir(parents=True, exist_ok=True)
                subject_info.raw_html_directory.mkdir(parents=True, exist_ok=True)
            
            # Initialize database
            await self.database_service.initialize_database()
            
            # Get browser instance
            browser = await self.browser_service.get_browser()
            
            try:
                # Scrape initial page
                init_result = await self._scrape_page(
                    browser=browser,
                    subject_info=subject_info,
                    config=config,
                    page_number="init"
                )
                page_results.append(init_result)
                total_problems_found += init_result.problems_found
                total_problems_saved += init_result.problems_saved
                
                # Determine last page number
                last_page_num = await self._determine_last_page(browser, subject_info.proj_id)
                
                # Scrape numbered pages
                page_num = 1
                empty_count = 0
                
                while True:
                    # Check if we've reached the last page
                    if last_page_num is not None and page_num > last_page_num:
                        logger.info(f"Reached determined last page ({last_page_num}). Stopping scraping.")
                        break
                    
                    # Check if we've hit max empty pages
                    if empty_count >= config.max_empty_pages:
                        logger.info(f"Reached {config.max_empty_pages} consecutive empty pages. Stopping scraping.")
                        break
                    
                    # Scrape current page
                    page_result = await self._scrape_page(
                        browser=browser,
                        subject_info=subject_info,
                        config=config,
                        page_number=str(page_num)
                    )
                    page_results.append(page_result)
                    total_problems_found += page_result.problems_found
                    total_problems_saved += page_result.problems_saved
                    
                    # Update empty page counter
                    if page_result.problems_found == 0:
                        empty_count += 1
                    else:
                        empty_count = 0
                    
                    page_num += 1
            
            finally:
                # Always release browser
                await self.browser_service.release_browser(browser)
            
            # Create final result
            end_time = datetime.now()
            success = total_problems_saved > 0 and len(errors) == 0
            
            return ScrapingSubjectResult(
                subject_name=subject_info.official_name,
                success=success,
                total_pages=len(page_results),
                total_problems_found=total_problems_found,
                total_problems_saved=total_problems_saved,
                page_results=page_results,
                errors=errors,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "subject_info": subject_info.to_dict(),
                    "config": config.to_dict(),
                    "browser_used": str(browser) if browser else "none"
                }
            )
            
        except Exception as e:
            logger.error(f"Scraping failed for {subject_info.official_name}: {e}", exc_info=True)
            errors.append(str(e))
            end_time = datetime.now()
            
            return ScrapingSubjectResult(
                subject_name=subject_info.official_name,
                success=False,
                total_pages=len(page_results),
                total_problems_found=total_problems_found,
                total_problems_saved=total_problems_saved,
                page_results=page_results,
                errors=errors,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "subject_info": subject_info.to_dict(),
                    "config": config.to_dict(),
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
    
    async def _scrape_page(
        self,
        browser: Any,
        subject_info: SubjectInfo,
        config: ScrapingConfig,
        page_number: str
    ) -> ScrapingPageResult:
        """
        Scrape a single page.
        
        Args:
            browser: Browser instance to use
            subject_info: Subject information
            config: Scraping configuration
            page_number: Page number to scrape
            
        Returns:
            ScrapingPageResult for the page
        """
        try:
            logger.debug(f"Scraping page '{page_number}' for subject {subject_info.official_name}")
            
            # Scrape the page
            problems, scraped_data = await self.page_scraping_service.scrape_page(
                proj_id=subject_info.proj_id,
                page_num=page_number,
                run_folder=subject_info.output_directory,
                subject=subject_info.subject_key,
                browser=browser,
                timeout=config.timeout_seconds
            )
            
            # Save problems to database
            saved_count = 0
            for problem in problems:
                try:
                    await self.database_service.save_problem(problem)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Failed to save problem {problem.problem_id}: {e}")
            
            # Create page result
            return ScrapingPageResult(
                page_number=page_number,
                success=True,
                problems_found=len(problems),
                problems_saved=saved_count,
                raw_html_path=scraped_data.get("raw_html_path"),
                metadata={
                    "scraped_data": scraped_data,
                    "subject_key": subject_info.subject_key,
                    "proj_id": subject_info.proj_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error scraping page {page_number} for {subject_info.official_name}: {e}", exc_info=True)
            return ScrapingPageResult(
                page_number=page_number,
                success=False,
                errors=[str(e)],
                metadata={
                    "subject_key": subject_info.subject_key,
                    "proj_id": subject_info.proj_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
    
    async def _determine_last_page(self, browser: Any, proj_id: str) -> Optional[int]:
        """
        Determine the last page number from the pager.
        
        Args:
            browser: Browser instance to use
            proj_id: Project ID for the subject
            
        Returns:
            Last page number if found, None otherwise
        """
        try:
            from infrastructure.adapters.database_adapter import config
            
            # Navigate to page 1 to get the pager information
            page = await browser.new_page()
            page_url = f"{config.FIPI_QUESTIONS_URL}?proj={proj_id}&page=1"
            
            await page.goto(page_url, wait_until="networkidle", timeout=30000)
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
                last_page_num = int(last_page_text)
                logger.info(f"Determined last page number: {last_page_num}")
                return last_page_num
            else:
                logger.warning(f"Could not determine last page number from pager, got: {last_page_text}")
                return None
                
        except Exception as e:
            logger.warning(f"Could not determine last page number from pager: {e}")
            return None
        finally:
            try:
                await page.close()
            except:
                pass
