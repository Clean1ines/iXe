"""
Module for pairing header containers and qblock elements in FIPI HTML pages.

This module provides the `ElementPairer` class which encapsulates the logic
for finding and matching corresponding header and content blocks.
"""
import logging
from typing import List, Tuple
from bs4 import BeautifulSoup
from bs4.element import Tag

logger = logging.getLogger(__name__)


class ElementPairer:
    """
    A class to pair 'header container' divs with their corresponding 'qblock' divs.

    This class provides a method to parse a BeautifulSoup object representing
    a FIPI page and find matching pairs of header and question blocks based
    on their order in the document structure.
    """

    def pair(self, page_soup: BeautifulSoup) -> List[Tuple[Tag, Tag]]:
        """
        Finds and pairs 'qblock' divs with their preceding/following 'header container' divs.

        Args:
            page_soup (BeautifulSoup): The parsed BeautifulSoup object of the page.

        Returns:
            List[Tuple[Tag, Tag]]: A list of tuples, where each tuple contains
                                (header_container_tag, qblock_tag).
        """
        logger.debug("Starting element pairing process.")
        qblocks = page_soup.find_all('div', class_='qblock')
        header_containers = page_soup.find_all('div', id=re.compile(r'^i'))
        logger.debug(f"Found {len(qblocks)} qblocks and {len(header_containers)} header containers for pairing.")

        body_children = page_soup.body.children if page_soup.body else []
        ordered_elements = []
        current_qblock_idx = 0
        current_header_idx = 0

        for child in body_children:
            if child.name == 'div':
                if child.get('class') and 'qblock' in child.get('class'):
                    if current_qblock_idx < len(qblocks):
                        ordered_elements.append(('qblock', qblocks[current_qblock_idx]))
                        current_qblock_idx += 1
                elif child.get('id') and child.get('id', '').startswith('i'):
                    if current_header_idx < len(header_containers):
                        ordered_elements.append(('header', header_containers[current_header_idx]))
                        current_header_idx += 1

        paired_elements = []
        i = 0
        while i < len(ordered_elements):
            if ordered_elements[i][0] == 'header' and i + 1 < len(ordered_elements) and ordered_elements[i + 1][0] == 'qblock':
                header_soup = ordered_elements[i][1]
                qblock_soup = ordered_elements[i + 1][1]
                paired_elements.append((header_soup, qblock_soup))
                i += 2
            elif ordered_elements[i][0] == 'qblock' and i + 1 < len(ordered_elements) and ordered_elements[i + 1][0] == 'header':
                qblock_soup = ordered_elements[i][1]
                header_soup = ordered_elements[i + 1][1]
                paired_elements.append((header_soup, qblock_soup))
                i += 2
            else:
                logger.warning(f"Unpaired element found at index {i}: {ordered_elements[i][0]}")
                i += 1

        logger.info(f"Successfully paired {len(paired_elements)} header-qblock sets.")
        return paired_elements
