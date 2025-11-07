"""Interface for HTML processors to ensure consistent processing pipeline."""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any
from pathlib import Path
from bs4 import BeautifulSoup


class IHTMLProcessor(ABC):
    """Interface for HTML processors."""

    @abstractmethod
    async def process(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Process HTML content.

        Args:
            content: Input HTML content as string
            context: Processing context with additional parameters

        Returns:
            Tuple of processed HTML content and metadata dictionary
        """
        pass
