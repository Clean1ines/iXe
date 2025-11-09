import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from bs4.element import Tag
from domain.interfaces.html_processor import IHTMLProcessor

class InputFieldRemover(IHTMLProcessor):
    """
    Removes input fields from the page content.
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
        This method removes input fields from the qblock content.
        """
        # Process the qblock content to remove input fields
        qblock_content = str(qblock)
        soup = BeautifulSoup(qblock_content, 'html.parser')
        
        # Remove input fields with name 'answer'
        for inp in soup.find_all('input', attrs={'name': 'answer'}):
            inp.decompose()
        
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
        Removes input fields with name 'answer'.

        Args:
            content: Input HTML content as string
            context: Processing context with additional parameters

        Returns:
            Tuple of processed HTML content and empty metadata dict.
        """
        soup = BeautifulSoup(content, 'html.parser')
        for inp in soup.find_all('input', attrs={'name': 'answer'}):
            inp.decompose()
        return str(soup), {}
