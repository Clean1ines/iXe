import re
from pathlib import Path
from bs4 import BeautifulSoup

class TaskInfoProcessor:
    """
    Processes task info buttons, updating onclick attributes.
    """
    async def process(self, soup: BeautifulSoup, run_folder_page: Path, downloader: 'AssetDownloader' = None, base_url: str = "", files_location_prefix: str = ""):
        """
        Updates onclick attributes for info buttons.

        Args:
            soup: BeautifulSoup object representing the page content.
            run_folder_page: Path to the page's run folder.
            downloader: AssetDownloader instance (not used here).
            base_url: Base URL (not used here).
            files_location_prefix: Prefix for file paths (not used here).

        Returns:
            Tuple of modified soup and empty metadata dict.
        """
        for button in soup.find_all('div', class_='info-button'):
            button['onclick'] = "toggleInfo(this); return false;"
        return soup, {}
