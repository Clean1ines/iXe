"""
Module for extracting task-specific metadata from HTML header containers.

This module provides the `MetadataExtractor` class which encapsulates the logic
for finding and extracting identifiers like task_id, form_id, task_number, kes_codes, and kos_codes from
FIPI page header elements.
"""
import logging
import re
from typing import Dict, List
from bs4 import BeautifulSoup
from bs4.element import Tag

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    A class to extract task-specific metadata (task_id, form_id, task_number, kes_codes, kos_codes) from header containers.

    This class provides a method to parse a BeautifulSoup Tag representing
    a header container and extract relevant identifiers.
    """

    def extract(self, header_container: Tag) -> Dict[str, any]:
        """
        Extracts task-specific metadata (task_id, form_id, task_number, kes_codes, kos_codes) from a header container.

        Args:
            header_container (Tag): The BeautifulSoup Tag representing the header container.

        Returns:
            Dict[str, any]: A dictionary containing 'task_id', 'form_id', 'task_number', 'kes_codes', 'kos_codes'.
                            Values are empty strings/lists if not found.
        """
        task_id = ""
        form_id = ""
        task_number = 0
        kes_codes = []
        kos_codes = []

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

        # Extract task_number from header_container text
        header_text = header_container.get_text(strip=False)
        task_number_match = re.search(r'(?:Задание|Task)\s+(\d+)', header_text, re.IGNORECASE)
        if task_number_match:
            task_number = int(task_number_match.group(1))
            logger.debug(f"Extracted task_number: {task_number}")

        # Extract kes_codes from header_container text and nearby elements
        kes_pattern = r'(?:КЭС|Кодификатор)[:\s]*([0-9.]+(?:\s*,\s*[0-9.]+)*)'
        kes_matches = re.findall(kes_pattern, header_text, re.IGNORECASE)
        if kes_matches:
            for match in kes_matches:
                codes = [code.strip() for code in match.split(',')]
                kes_codes.extend(codes)
            kes_codes = list(set(kes_codes))  # Remove duplicates
            logger.debug(f"Extracted kes_codes: {kes_codes}")

        # Extract kos_codes from header_container text and nearby elements
        kos_pattern = r'(?:КОС|Требование)[:\s]*([0-9.]+(?:\s*,\s*[0-9.]+)*)'
        kos_matches = re.findall(kos_pattern, header_text, re.IGNORECASE)
        if kos_matches:
            for match in kos_matches:
                codes = [code.strip() for code in match.split(',')]
                kos_codes.extend(codes)
            kos_codes = list(set(kos_codes))  # Remove duplicates
            logger.debug(f"Extracted kos_codes: {kos_codes}")

        return {
            "task_id": task_id,
            "form_id": form_id,
            "task_number": task_number,
            "kes_codes": kes_codes,
            "kos_codes": kos_codes
        }
