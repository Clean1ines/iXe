# application/services/page_scraping_service.py
"""
Application service for scraping a single page of problems.
Implements the use case: ScrapePageForSubject
"""
from typing import List, Tuple, Dict, Any
from pathlib import Path
from domain.interfaces.html_processor import IHTMLProcessor
from domain.interfaces.infrastructure_adapters import IDatabaseProvider
from domain.models.problem_schema import Problem as PydanticProblem
from utils.fipi_urls import FIPI_QUESTIONS_URL
from datetime import datetime
import logging
import asyncio
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from application.factories.problem_factory import ProblemFactory  # Импорт фабрики


logger = logging.getLogger(__name__)


class PageScrapingService:
    def __init__(
        self,
        html_processor: IHTMLProcessor,
        problem_repo: IDatabaseProvider,
        browser_manager,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        problem_factory: ProblemFactory = None  # Добавляем фабрику как зависимость
    ):
        self._html_processor = html_processor
        self._problem_repo = problem_repo
        self._browser_manager = browser_manager
        self._max_retries = max_retries
        self._initial_delay = initial_delay
        # Используем переданную фабрику или создаем новую
        self._problem_factory = problem_factory or ProblemFactory()

    async def scrape_page(
        self,
        proj_id: str,
        page_num: str,
        run_folder: Path,
        subject: str,
    ) -> Tuple[List[PydanticProblem], Dict[str, Any]]:
        """
        Application use case: scrape a single page of problems.
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
            
            # Process the page content using the existing orchestrator
            run_folder_page = run_folder / page_num
            
            from processors.page_processor import PageProcessingOrchestrator
            orchestrator = PageProcessingOrchestrator(html_processor=self._html_processor)
            
            results = await orchestrator.process_page(
                page_content=page_content,
                subject=subject,
                base_url=base_questions_url,
                run_folder_page=run_folder_page,
                # Use the correct downloader from utils.downloader
                downloader=self._create_asset_downloader(page),
                files_location_prefix="../../"
            )
            
            # Convert results to Pydantic Problem objects and save
            pydantic_problems = []
            domain_problems = []
            
            for result in results:
                # Создаем Pydantic проблему
                pydantic_problem = self._create_problem_from_result(result, subject)
                pydantic_problems.append(pydantic_problem)
                
                # Преобразуем в DomainProblem и сохраняем
                if self._problem_repo is not None:
                    try:
                        domain_problem = self._problem_factory.from_pydantic(pydantic_problem)
                        domain_problems.append(domain_problem)
                        
                        await self._problem_repo.save_problem(domain_problem)
                        logger.info(f"Saved domain problem {domain_problem.problem_id.value} to database")
                    except Exception as e:
                        logger.error(f"Failed to save problem {pydantic_problem.problem_id}: {e}")
                        logger.error(f"Pydantic problem  {pydantic_problem.model_dump()}")
                        continue  # Продолжаем с другими проблемами
            
            scraped_data = {
                "page_name": page_num,
                "url": full_url,
                "results": results
            }
            
            logger.info(f"Successfully scraped {len(pydantic_problems)} problems from page {page_num}")
            return pydantic_problems, scraped_data
            
        finally:
            # Close the page
            await page.close()
    
    def _create_asset_downloader(self, page):
        """Create an asset downloader instance."""
        from utils.downloader import AssetDownloader
        return AssetDownloader(page=page)

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

    def _create_problem_from_result(self, result: Dict[str, Any], subject: str) -> PydanticProblem:
        """Create Pydantic Problem instance from processing result."""
        # Ensure problem_id is properly formatted according to Pydantic model expectations
        raw_problem_id = result.get('problem_id', f"{subject}_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Format problem_id to match expected pattern: subject_tasknumber_year_n
        task_number = result.get('task_number', 1)  # Default to 1 if not provided
        year = "2025"  # Default year
        
        # Try to extract task number from raw ID if it looks like a task ID
        if '_' in raw_problem_id:
            parts = raw_problem_id.split('_')
            if len(parts) >= 2:
                # Look for a numeric task number in the parts
                for part in parts:
                    if part.isdigit():
                        task_number = int(part)
                        break
                    # Also look for patterns like "task1", "1task", etc.
                    elif part.replace('task', '').replace('Task', '').isdigit():
                        task_number = int(part.replace('task', '').replace('Task', ''))
                        break
        
        # Create properly formatted problem_id
        problem_id = f"{subject}_{task_number}_{year}_1"
        
        # Ensure exam_part is valid
        exam_part = result.get('exam_part', 'Part 1')
        if exam_part not in ['Part 1', 'Part 2']:
            exam_part = 'Part 1'  # Default value
        
        # Ensure max_score is valid
        max_score = result.get('max_score', 1)
        if not isinstance(max_score, int) or max_score <= 0:
            max_score = 1  # Default value
        
        # Ensure task_number is valid
        task_number = result.get('task_number', 1)
        if not isinstance(task_number, int):
            task_number = 1  # Default value
        
        # Ensure difficulty_level is valid
        difficulty_level = result.get('difficulty_level', 'basic')
        if difficulty_level not in ['basic', 'intermediate', 'advanced']:
            difficulty_level = 'basic'  # Default value
        
        # Ensure type is valid (critical fix!)
        problem_type = result.get('type', 'unknown')
        if not problem_type:
            problem_type = 'unknown'
        
        # Use kes_codes as topics for DB compatibility
        kes_codes = result.get('kes_codes', [])
        
        # Create the Pydantic Problem with all required string/int fields
        return PydanticProblem(
            problem_id=problem_id,
            subject=subject,
            type=problem_type,  # Critical fix: ensure type is always present
            text=result.get('text', ''),
            difficulty_level=difficulty_level,
            exam_part=exam_part,
            max_score=max_score,
            task_number=task_number,
            # Optional fields with defaults
            answer=result.get('answer'),
            options=result.get('options', []),
            solutions=result.get('solutions'),
            kes_codes=kes_codes,
            skills=result.get('skills'),
            kos_codes=result.get('kos_codes', []),
            form_id=result.get('form_id'),
            source_url=result.get('source_url'),
            raw_html_path=result.get('raw_html_path'),
            created_at=result.get('created_at', datetime.now()),
            updated_at=result.get('updated_at'),
            metadata=result.get('metadata')
        )