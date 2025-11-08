import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from domain.interfaces.html_processor import IHTMLProcessor

class MathMLRemover(IHTMLProcessor):
    """
    Removes MathML elements from the page content.
    """
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
