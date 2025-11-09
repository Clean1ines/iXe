import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from bs4.element import Tag
from domain.interfaces.html_processor import IHTMLProcessor

class MathMLRemover(IHTMLProcessor):
    """
    Removes MathML elements from the page content.
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
        This method removes MathML elements from the qblock content.
        """
        # Process the qblock content to remove MathML
        qblock_content = str(qblock)
        soup = BeautifulSoup(qblock_content, 'html.parser')
        
        # Remove math and mml:math tags
        for tag in soup.find_all(['math', 'mml:math']):
            tag.decompose()
        
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
        Removes math and mml:math tags.

        Args:
            content: Input HTML content as string
            context: Processing context with additional parameters

        Returns:
            Tuple of processed HTML content and empty metadata dict.
        """
        soup = BeautifulSoup(content, 'html.parser')
        for tag in soup.find_all(['math', 'mml:math']):
            tag.decompose()
        return str(soup), {}
