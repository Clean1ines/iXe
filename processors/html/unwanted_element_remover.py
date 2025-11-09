import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from bs4.element import Tag
from domain.interfaces.html_processor import IHTMLProcessor

class UnwantedElementRemover(IHTMLProcessor):
    """
    Removes unwanted HTML elements from the page content.
    """
    
    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str,
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and return structured data.
        This method removes unwanted elements from the qblock content.
        """
        # Process the qblock content to remove unwanted elements
        qblock_content = str(qblock)
        soup = BeautifulSoup(qblock_content, 'html.parser')
        
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
        
        # Update the qblock with processed content
        processed_qblock = soup.find('div', class_='qblock') or soup.find('div')
        
        # Return the processed block data
        return {
            'header_container': header_container,
            'qblock': processed_qblock,
            'block_index': block_index,
            'subject': subject,
            'base_url': base_url
        }

    async def process(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Removes hint divs, status title spans, task status spans, and table rows with bgcolor.

        Args:
            content: Input HTML content as string
            context: Processing context with additional parameters
                - 'run_folder_page': Path to the page's run folder

        Returns:
            Tuple of modified HTML content and metadata dict.
        """
        run_folder_page = context.get('run_folder_page')
        
        soup = BeautifulSoup(content, 'html.parser')
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
        
        return str(soup), {}
