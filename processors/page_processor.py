"""
Module for orchestrating the processing of a single scraped HTML page into structured data.
This module provides the `PageProcessingOrchestrator` class which coordinates the parsing,
pairing, metadata extraction, asset downloading, and HTML transformation steps required
to convert raw FIPI page content into a list of structured data dictionaries.
"""
import logging
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup
from utils.downloader import AssetDownloader
from infrastructure.adapters.html_pairer_adapter import HTMLPairerAdapter
from domain.interfaces.html_processor import IHTMLProcessor


logger = logging.getLogger(__name__)


class PageProcessingOrchestrator:
    """
    Orchestrates the processing of a complete HTML page into structured data.
    
    It handles the entire pipeline from raw HTML string to a list of structured data dictionaries.
    """

    def __init__(
        self,
        html_processor: IHTMLProcessor,
    ):
        """
        Initializes the orchestrator with required services.

        Args:
            html_processor: IHTMLProcessor implementation for processing HTML blocks
        """
        self.html_processor = html_processor
        self.pairer = HTMLPairerAdapter()

    async def process_page(
        self,
        page_content: str,
        subject: str,
        base_url: str,
        run_folder_page: Path,
        downloader: AssetDownloader,
        files_location_prefix: str = "",
    ) -> List[dict]:
        """
        Processes the entire page content into a list of structured data dictionaries.

        Args:
            page_content: The raw HTML string of the page.
            subject: The subject name (e.g., "math", "informatics").
            base_url: The base URL of the scraped page.
            run_folder_page: Path to the run folder for this page's assets.
            downloader: AssetDownloader instance for downloading files.
            files_location_prefix: Prefix for file paths in the output.

        Returns:
            A list of structured data dictionaries extracted from the page.
        """
        logger.info(f"Starting to process page for subject '{subject}' with {len(page_content)} characters of content.")

        soup = BeautifulSoup(page_content, 'html.parser')
        paired_elements = self.pairer.pair_elements(soup)

        results = []
        for i, (header_container, qblock) in enumerate(paired_elements):
            result = await self.html_processor.process_html_block(
                header_container=header_container,
                qblock=qblock,
                block_index=i,
                subject=subject,
                base_url=base_url,
                run_folder_page=run_folder_page,
                downloader=downloader,
                files_location_prefix=files_location_prefix,
            )
            results.append(result)

        logger.info(f"Completed processing page for subject '{subject}'. Generated {len(results)} results.")
        return results
