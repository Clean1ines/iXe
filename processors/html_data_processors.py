"""
Module for processing HTML data and extracting content.

This module provides various processors for handling different aspects of HTML content
including images, file links, task information, input fields, and MathML elements.
All processors implement the `AssetProcessor` interface.
"""

import re
from pathlib import Path
from typing import Any, Dict, Tuple
from bs4 import BeautifulSoup
from processors.asset_processor_interface import AssetProcessor


class ImageScriptProcessor(AssetProcessor):
    """
    A class to process image-related scripts in HTML content.

    This processor finds scripts containing ShowPicture function calls,
    downloads the referenced images, and replaces the scripts with img tags.
    Implements the `AssetProcessor` interface.
    """

    def process(self, soup: BeautifulSoup, assets_dir: Path, **kwargs) -> Tuple[BeautifulSoup, Dict[str, Any]]:
        """
        Processes script tags containing ShowPicture calls and replaces them with img tags.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.
            assets_dir (Path): The directory where downloaded assets should be saved.
                               Relative paths in the returned metadata are relative to
                               the parent of this directory (i.e., the HTML page directory).
            **kwargs: Must contain 'downloader': an instance of `AssetDownloader`.

        Returns:
            Tuple[BeautifulSoup, Dict[str, Any]]: A tuple containing:
                - Updated BeautifulSoup object with scripts replaced by img tags.
                - Dictionary mapping original image sources to local relative paths,
                  under the key 'downloaded_images'.
        """
        downloader = kwargs.get('downloader')
        if not downloader:
            raise ValueError("AssetDownloader must be provided via kwargs['downloader']")

        downloaded_images = {}
        pattern = re.compile(r'ShowPicture\w*\s*\(\s*[\'"]([^\'"]+)[\'"]', re.IGNORECASE)

        for script_tag in soup.find_all('script', string=pattern):
            script_text = script_tag.get_text()
            match = pattern.search(script_text)

            if match:
                img_src = match.group(1)
                # Pass assets_dir / "assets" to downloader
                local_path = downloader.download(img_src, assets_dir / "assets", asset_type='image')

                if local_path:
                    # Calculate path relative to the HTML file's directory (assets_dir.parent)
                    path_relative_to_html = str(local_path.relative_to(assets_dir))

                    # Create new img tag
                    new_img = soup.new_tag('img', src=path_relative_to_html)
                    script_tag.replace_with(new_img)

                    downloaded_images[img_src] = path_relative_to_html

        return soup, {"downloaded_images": downloaded_images}


class FileLinkProcessor(AssetProcessor):
    """
    A class to process file download links in HTML content.

    This processor finds file links (both JavaScript window.open calls and direct links),
    downloads the referenced files, and updates the links to point to local copies.
    Implements the `AssetProcessor` interface.
    """

    def process(self, soup: BeautifulSoup, assets_dir: Path, **kwargs) -> Tuple[BeautifulSoup, Dict[str, Any]]:
        """
        Processes file download links and downloads the referenced files.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.
            assets_dir (Path): The directory where downloaded assets should be saved.
                               Relative paths in the returned metadata are relative to
                               the parent of this directory (i.e., the HTML page directory).
            **kwargs: Must contain 'downloader': an instance of `AssetDownloader`.

        Returns:
            Tuple[BeautifulSoup, Dict[str, Any]]: A tuple containing:
                - Updated BeautifulSoup object with file links pointing to local copies.
                - Dictionary mapping original file URLs to local relative paths,
                  under the key 'downloaded_files'.
        """
        downloader = kwargs.get('downloader')
        if not downloader:
            raise ValueError("AssetDownloader must be provided via kwargs['downloader']")

        downloaded_files = {}
        file_extensions = r'\.(zip|rar|pdf|doc|docx|xls|xlsx)$'

        for a_tag in soup.find_all('a'):
            href = a_tag.get('href')
            if not href:
                continue

            file_path = None

            # Handle JavaScript links with window.open
            if href.startswith('javascript:'):
                match = re.search(r"window\.open\(\s*['\"]([^'\"]+)['\"]", href, re.IGNORECASE)
                if match:
                    file_path = match.group(1)
                    # Remove leading ../../
                    file_path = file_path.lstrip('../../')

            # Handle direct file links
            elif re.search(file_extensions, href, re.IGNORECASE):
                file_path = href.lstrip('../../')

            if file_path:
                # Pass assets_dir / "assets" to downloader
                local_path = downloader.download(file_path, assets_dir / "assets", asset_type='file')

                if local_path:
                    # Calculate path relative to the HTML file's directory (assets_dir.parent)
                    path_relative_to_html = str(local_path.relative_to(assets_dir))

                    # Update the href to point to local file
                    a_tag['href'] = path_relative_to_html
                    downloaded_files[file_path] = path_relative_to_html

        return soup, {"downloaded_files": downloaded_files}


class TaskInfoProcessor(AssetProcessor):
    """
    A class to process task information buttons in HTML content.

    This processor updates the onclick handlers for info buttons to work
    in standalone HTML files.
    Implements the `AssetProcessor` interface.
    """

    def process(self, soup: BeautifulSoup, assets_dir: Path, **kwargs) -> Tuple[BeautifulSoup, Dict[str, Any]]:
        """
        Updates info button onclick handlers for standalone HTML compatibility.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.
            assets_dir (Path): Not used by this processor.
            **kwargs: Not used by this processor.

        Returns:
            Tuple[BeautifulSoup, Dict[str, Any]]: A tuple containing:
                - Updated BeautifulSoup object with modified info buttons.
                - Empty metadata dictionary.
        """
        for info_button in soup.find_all('div', class_='info-button'):
            info_button['onclick'] = "toggleInfo(this); return false;"

        return soup, {}


class InputFieldRemover(AssetProcessor):
    """
    A class to remove answer input fields from HTML content.

    This processor removes the original FIPI answer input fields that are
    not needed in the processed output.
    Implements the `AssetProcessor` interface.
    """

    def process(self, soup: BeautifulSoup, assets_dir: Path, **kwargs) -> Tuple[BeautifulSoup, Dict[str, Any]]:
        """
        Removes answer input fields from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.
            assets_dir (Path): Not used by this processor.
            **kwargs: Not used by this processor.

        Returns:
            Tuple[BeautifulSoup, Dict[str, Any]]: A tuple containing:
                - Updated BeautifulSoup object without answer input fields.
                - Empty metadata dictionary.
        """
        for input_tag in soup.find_all('input', attrs={'name': 'answer'}):
            input_tag.decompose()

        return soup, {}


class MathMLRemover(AssetProcessor):
    """
    A class to remove MathML elements from HTML content.

    This processor removes MathML tags to allow proper rendering with MathJax
    or other math rendering libraries.
    Implements the `AssetProcessor` interface.
    """

    def process(self, soup: BeautifulSoup, assets_dir: Path, **kwargs) -> Tuple[BeautifulSoup, Dict[str, Any]]:
        """
        Removes MathML elements from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.
            assets_dir (Path): Not used by this processor.
            **kwargs: Not used by this processor.

        Returns:
            Tuple[BeautifulSoup, Dict[str, Any]]: A tuple containing:
                - Updated BeautifulSoup object without MathML elements.
                - Empty metadata dictionary.
        """
        for math_tag in soup.find_all(['math', 'mml:math']):
            math_tag.decompose()

        return soup, {}


class UnwantedElementRemover(AssetProcessor):
    """
    A class to remove unwanted elements from HTML content.

    This processor removes specific elements that are not needed in the processed output,
    such as hint divs, status spans, and submission tables.
    Implements the `AssetProcessor` interface.
    """

    def process(self, soup: BeautifulSoup, assets_dir: Path, **kwargs) -> Tuple[BeautifulSoup, Dict[str, Any]]:
        """
        Removes unwanted elements from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.
            assets_dir (Path): Not used by this processor.
            **kwargs: Not used by this processor.

        Returns:
            Tuple[BeautifulSoup, Dict[str, Any]]: A tuple containing:
                - Updated BeautifulSoup object without unwanted elements.
                - Empty metadata dictionary.
        """
        # Remove hint div with specific content
        hint_div = soup.find('div', attrs={'class': 'hint', 'id': 'hint', 'name': 'hint'}, string='Впишите правильный ответ.')
        if hint_div:
            hint_div.decompose()

        # Remove status title span with specific content
        status_title_span = soup.find('span', attrs={'class': 'status-title-text hidden-xs'}, string='Статус задания:')
        if status_title_span:
            status_title_span.decompose()

        # Remove task status span with dynamic class containing 'task-status' and 'task-status-'
        for span in soup.find_all('span', string='НЕ РЕШЕНО'):
            class_attr = span.get('class', [])
            if class_attr and any('task-status' in cls and 'task-status-' in cls for cls in class_attr):
                span.decompose()

        # Remove table row with bgcolor="#FFFFFF"
        tr_with_bgcolor = soup.find('tr', attrs={'bgcolor': '#FFFFFF'})
        if tr_with_bgcolor:
            tr_with_bgcolor.decompose()

        # DO NOT remove <span class="canselect"> — needed for task ID extraction
        # DO NOT remove <span class="answer-button"> — needed for form ID extraction

        return soup, {}
