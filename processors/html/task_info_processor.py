import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from processors.html_processor_interface import IHTMLProcessor

class TaskInfoProcessor(IHTMLProcessor):
    """
    Processes task info buttons, updating onclick attributes.
    """
    async def process(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Updates onclick attributes for info buttons.

        Args:
            content: Input HTML content as string
            context: Processing context with additional parameters

        Returns:
            Tuple of processed HTML content and empty metadata dict.
        """
        soup = BeautifulSoup(content, 'html.parser')
        for button in soup.find_all('div', class_='info-button'):
            button['onclick'] = "toggleInfo(this); return false;"
        return str(soup), {}
