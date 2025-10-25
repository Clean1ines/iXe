"""
Module for extracting task-specific metadata from HTML header containers.

This module provides the `MetadataExtractor` class which encapsulates the logic
for finding and extracting identifiers like task_id and form_id from
FIPI page header elements.
"""
import logging
import re
from typing import Dict
from bs4 import BeautifulSoup
from bs4.element import Tag

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    A class to extract task-specific metadata (task_id, form_id) from header containers.

    This class provides a method to parse a BeautifulSoup Tag representing
    a header container and extract relevant identifiers.
    """

    def extract(self, header_container: Tag) -> Dict[str, str]:
        """
        Extracts task-specific metadata (task_id, form_id) from a header container.

        Args:
            header_container (Tag): The BeautifulSoup Tag representing the header container.

        Returns:
            Dict[str, str]: A dictionary containing 'task_id' and 'form_id'.
                            Values are empty strings if not found.
        """
        task_id = ""
        form_id = ""
        # Extract task_id
        canselect_span = header_container.find('span', class_='canselect')
        if canselect_span:
            task_id = canselect_span.get_text(strip=True)
        logger.debug(f"Extracted task_id: '{task_id}'")
        # Extract form_id
        answer_button = header_container.find('span', class_='answer-button')
        if answer_button and answer_button.get('onclick'):
            onclick = answer_button['onclick']
            form_match = re.search(r"checkButtonClick\(\s*['\"]([^'\"]+)['\"]", onclick)
            if form_match:
                form_id = form_match.group(1)
                logger.debug(f"Extracted form_id: '{form_id}'")
        return {"task_id": task_id, "form_id": form_id}
