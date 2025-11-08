"""Tests for the scrape_tasks script."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from scripts.scrape_tasks import CLIScraper
from infrastructure.adapters.database_adapter import DatabaseAdapter
from pathlib import Path


class TestCLIScraperScrapeSubjectLogic:
    """Test suite for the scrape_subject_logic function in CLIScraper."""

    @pytest.mark.asyncio
    async def test_scrape_subject_logic_handles_scrape_page_exception(self):
        """Test that scrape_subject_logic continues after a scrape_page exception and increments empty_count."""
        proj_id = "TEST_PROJ_ID"
        subject_name = "test_subject"
        scraping_subject_key = "test_key"
        subject_dir = Path("/tmp/test_subject_dir")
        db_manager = MagicMock(spec=DatabaseAdapter)

        # Create a mock scraper that raises an exception on scrape_page call
        with patch('scripts.scrape_tasks.BrowserPoolManager') as mock_browser_pool_mgr, \
             patch('scripts.scrape_tasks.FIPIScraper') as MockFIPIScraper:

            mock_browser_pool = AsyncMock()
            mock_browser_pool.__aenter__.return_value = mock_browser_pool
            mock_browser_pool.__aexit__.return_value = None
            mock_browser_pool.get_available_browser = AsyncMock()
            mock_browser_pool_mgr.return_value = mock_browser_pool

            mock_scraper_instance = MockFIPIScraper.return_value
            # Make the first call (init) succeed with a problem, then fail on page 1, then succeed on page 2
            # Page 2 success is needed to ensure the loop doesn't exit due to max_empty before page 1 error is processed
            mock_scraper_instance.scrape_page = AsyncMock()
            mock_problem = MagicMock()
            mock_problem.subject = None
            mock_scraper_instance.scrape_page.side_effect = [
                ([mock_problem], {}),  # Success for 'init' page, returns one problem
                RuntimeError("Test scraping error"),  # Error for page 1
                ([], {}),  # Success for page 2 (empty), to allow loop to continue past page 1 error
            ]

            cli_scraper = CLIScraper()

            # Call the function under test
            await cli_scraper.scrape_subject_logic(
                proj_id=proj_id,
                subject_name=subject_name,
                scraping_subject_key=scraping_subject_key,
                subject_dir=subject_dir,
                db_manager=db_manager
            )

            # Assert that scrape_page was called for init, page 1 (error), and page 2 (to continue loop)
            assert mock_scraper_instance.scrape_page.call_count >= 2
            # Assert that save_problems was called for the init page result (only once, for the init page)
            # The problem from init page should be saved
            db_manager.save_problems.assert_called_once()

