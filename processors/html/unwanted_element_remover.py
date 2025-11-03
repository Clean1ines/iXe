import re
from pathlib import Path
from bs4 import BeautifulSoup

class UnwantedElementRemover:
    """
    Removes unwanted HTML elements from the page content.
    """
    def process(self, soup: BeautifulSoup, run_folder_page: Path):
        """
        Removes hint divs, status title spans, task status spans, and table rows with bgcolor.

        Args:
            soup: BeautifulSoup object representing the page content.
            run_folder_page: Path to the page's run folder.

        Returns:
            Tuple of modified soup and empty metadata dict.
        """
        downloaded_files = {}
        downloaded_images = {}
        # Remove hint divs
        for div in soup.find_all('div', class_=re.compile(r'hint'), attrs={'id': 'hint', 'name': 'hint'}):
            div.decompose()
        # Remove status title spans
        for span in soup.find_all('span', class_=re.compile(r'status-title-text')):
            span.decompose()
        # Remove task status spans
        for span in soup.find_all('span', class_=re.compile(r'task-status')):
            span.decompose()
        # Remove table rows with bgcolor
        for tr in soup.find_all('tr', attrs={'bgcolor': '#FFFFFF'}):
            tr.decompose()
        return soup, {}
