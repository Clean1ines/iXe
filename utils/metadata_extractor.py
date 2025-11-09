"""
Module for extracting task-specific metadata from HTML header containers.

This module provides the `MetadataExtractor` class which encapsulates the logic
for finding and extracting identifiers like task_id and form_id from
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
    A class to extract task-specific metadata (task_id, form_id) from header containers.

    This class provides a method to parse a BeautifulSoup Tag representing
    a header container and extract relevant identifiers.
    """

    def extract(self, header_container: Tag) -> Dict[str, str | int | List[str]]:
        """
        Extracts task-specific metadata from a header container.

        Args:
            header_container (Tag): The BeautifulSoup Tag representing the header container.

        Returns:
            Dict[str, Union[str, int, List[str]]]: A dictionary containing:
                - 'task_id' (str): Identifier from the 'canselect' span.
                - 'task_number' (int): Extracted task number from patterns like "Задание N" or "Task N".
                - 'kes_codes' (List[str]): List of КЭС codes (e.g., from "КЭС: 2.1" or "Кодификатор: 2.1.1").
                - 'kos_codes' (List[str]): List of КОС codes (e.g., from "КОС: 3" or "Требование: 3.1").
                Missing or unparsable values are replaced with defaults (empty string, 0, or empty list).
                'form_id' is no longer extracted here and will be provided separately based on qblock id.
        """
        task_id = ""
        task_number = 0
        kes_codes: List[str] = []
        kos_codes: List[str] = []

        # --- Existing logic: task_id ---
        canselect_span = header_container.find('span', class_='canselect')
        if canselect_span:
            task_id = canselect_span.get_text(strip=True)
        logger.debug(f"Extracted task_id: '{task_id}'")

        # --- New logic: task_number ---
        header_text = header_container.get_text(separator=' ', strip=True)
        task_number_match = re.search(r'(?:Задание|Task)\s+(\d+)', header_text, re.IGNORECASE)
        if task_number_match:
            try:
                task_number = int(task_number_match.group(1))
                logger.debug(f"Extracted task_number: {task_number}")
            except ValueError:
                logger.warning(f"Failed to parse task number from match: {task_number_match.group(0)}")
        else:
            logger.debug("task_number pattern not found in header text")

        # --- New logic: kes_codes ---
        # Patterns: "КЭС: 2.1", "Кодификатор: 2.1.1", possibly multiple codes separated by commas or spaces
        kes_patterns = [
            r'КЭС\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)',
            r'Кодификатор\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)'
        ]
        for pattern in kes_patterns:
            matches = re.findall(pattern, header_text, re.IGNORECASE)
            if matches:
                kes_codes.extend(matches)
                logger.debug(f"Found КЭС matches with pattern '{pattern}': {matches}")
        kes_codes = list(set(kes_codes))  # deduplicate
        logger.debug(f"Final kes_codes: {kes_codes}")

        # --- New logic: kos_codes ---
        # Patterns: "КОС: 3", "Требование: 3.1"
        kos_patterns = [
            r'КОС\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)',
            r'Требование\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)'
        ]
        for pattern in kos_patterns:
            matches = re.findall(pattern, header_text, re.IGNORECASE)
            if matches:
                kos_codes.extend(matches)
                logger.debug(f"Found КОС matches with pattern '{pattern}': {matches}")
        kos_codes = list(set(kos_codes))  # deduplicate
        logger.debug(f"Final kos_codes: {kos_codes}")

        return {
            "task_id": task_id,
            "task_number": task_number,
            "kes_codes": kes_codes,
            "kos_codes": kos_codes
            # 'form_id' больше не извлекается здесь
        }

    def extract_metadata_from_header(self, header_container: Tag) -> Dict[str, any]:
        """
        Extracts metadata from a header container specifically for the BlockProcessorAdapter.
        This method maintains compatibility with the existing codebase that calls
        extract_metadata_from_header on MetadataExtractor instances.
        
        Args:
            header_container (Tag): The BeautifulSoup Tag representing the header container.

        Returns:
            Dict[str, any]: A dictionary containing extracted metadata.
        """
        return self.extract(header_container)
