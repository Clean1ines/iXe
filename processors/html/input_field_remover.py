import re
from pathlib import Path
from bs4 import BeautifulSoup

class InputFieldRemover:
    """
    Removes input fields from the page content.
    """
    def process(self, soup: BeautifulSoup, run_folder_page: Path, downloader: 'AssetDownloader' = None, base_url: str = "", files_location_prefix: str = ""):
        """
        Removes input fields with name 'answer'.

        Args:
            soup: BeautifulSoup object representing the page content.
            run_folder_page: Path to the page's run folder.
            downloader: AssetDownloader instance (not used here).
            base_url: Base URL (not used here).
            files_location_prefix: Prefix for file paths (not used here).

        Returns:
            Tuple of modified soup and empty metadata dict.
        """
        for inp in soup.find_all('input', attrs={'name': 'answer'}):
            inp.decompose()
        return soup, {}
