import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from processors.html_processor_interface import IHTMLProcessor

class InputFieldRemover(IHTMLProcessor):
    """
    Removes input fields from the page content.
    """
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
