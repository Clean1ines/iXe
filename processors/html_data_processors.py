"""
Module containing HTML data processors for various content types.

This module provides processor classes for handling different types of
content found in FIPI pages: images embedded in <script> tags, file links,
task metadata panels, and general cleanup operations. Each processor
implements a `process` method that transforms the input HTML and returns
processed content along with extracted metadata.
"""
import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
from bs4.element import Tag

logger = logging.getLogger(__name__)


class ImageScriptProcessor:
    """
    Processor for extracting and replacing image data embedded in JavaScript.

    This processor locates <script> tags containing Base64-encoded images,
    downloads them to the local filesystem, and replaces the script content
    with standard <img> tags pointing to the local files.
    """

    def __init__(self):
        self.downloader = None  # Will be set externally or via factory

    async def process(
        self, soup: BeautifulSoup, assets_dir: Path, **kwargs
    ) -> Tuple[BeautifulSoup, Dict[str, str]]:
        """
        Process a BeautifulSoup object to extract and replace image scripts.

        Args:
            soup (BeautifulSoup): Parsed HTML content to process.
            assets_dir (Path): Directory where downloaded images should be saved.
            **kwargs: Additional arguments, including 'downloader' for downloading assets.

        Returns:
            Tuple[BeautifulSoup, Dict[str, str]]:
                - Modified soup with script tags replaced by img tags
                - Dictionary mapping original asset URLs to local file paths
        """
        logger.debug("Starting ImageScriptProcessor...")
        downloader = kwargs.get('downloader')
        base_url = kwargs.get('base_url', '')
        files_location_prefix = kwargs.get('files_location_prefix', '../../')
        downloaded_images = {}
        scripts = soup.find_all('script')
        script_counter = 0
        for script in scripts:
            if script.string and ('src:' in script.string or 'image' in script.string):
                # Try to extract JSON-like structure
                try:
                    clean_str = re.sub(r'[\n\r\t]', '', script.string)
                    json_match = re.search(r'\{[^}]*"src"\s*:\s*"[^"]+"[^}]*\}', clean_str)
                    if json_match:
                        json_str = json_match.group()
                        data = json.loads(json_str)
                        asset_url = data.get('src')
                        alt_text = data.get('alt', '')
                        if asset_url and asset_url.startswith('image'):
                            # Handle Base64 encoded image
                            header, encoded = asset_url.split(',', 1)
                            extension = header.split(';')[0].split('/')[-1] or 'png'
                            img_name = f"embedded_img_{script_counter}.{extension}"
                            img_path = assets_dir / "embedded_images" / img_name
                            img_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(img_path, 'wb') as f:
                                f.write(base64.b64decode(encoded))
                            relative_path = files_location_prefix + str(img_path.relative_to(assets_dir.parent))
                            new_img_tag = soup.new_tag('img', src=relative_path, alt=alt_text)
                            script.replace_with(new_img_tag)
                            downloaded_images[asset_url] = str(img_path)
                            script_counter += 1
                        elif asset_url:
                            # Handle regular URL, download it
                            if not asset_url.startswith(('http', '//')):
                                asset_url = urljoin(base_url, asset_url)
                            if downloader:
                                saved_path = await downloader.download(asset_url, assets_dir / "embedded_images", asset_type='image')
                                if saved_path:
                                    relative_path = files_location_prefix + str(saved_path.relative_to(assets_dir.parent))
                                    new_img_tag = soup.new_tag('img', src=relative_path, alt=alt_text)
                                    script.replace_with(new_img_tag)
                                    downloaded_images[asset_url] = str(saved_path)
                                    script_counter += 1
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse script content as JSON: {e}")
                    continue
        return soup, {'downloaded_images': downloaded_images}


class FileLinkProcessor:
    """
    Processor for downloading and replacing links to external files.

    This processor finds links to documents (PDF, DOC, etc.), downloads them
    to the local filesystem, and updates the href attributes to point to the
    local copies. It also handles inline file data URIs.
    """

    def __init__(self):
        self.downloader = None  # Will be set externally or via factory

    async def process(
        self, soup: BeautifulSoup, assets_dir: Path, **kwargs
    ) -> Tuple[BeautifulSoup, Dict[str, str]]:
        """
        Process a BeautifulSoup object to download and replace file links.

        Args:
            soup (BeautifulSoup): Parsed HTML content to process.
            assets_dir (Path): Directory where downloaded files should be saved.
            **kwargs: Additional arguments, including 'downloader' for downloading assets.

        Returns:
            Tuple[BeautifulSoup, Dict[str, str]]:
                - Modified soup with updated file links
                - Dictionary mapping original file URLs to local file paths
        """
        logger.debug("Starting FileLinkProcessor...")
        downloader = kwargs.get('downloader')
        base_url = kwargs.get('base_url', '')
        files_location_prefix = kwargs.get('files_location_prefix', '../../')
        downloaded_files = {}
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            parsed_url = urlparse(href)
            if parsed_url.scheme == 'data':
                # Handle data URI
                if 'application/pdf' in href or href.startswith('data:application/pdf'):
                    try:
                        header, encoded = href.split(',', 1)
                        file_name = f"embedded_doc_{len(downloaded_files)}.pdf"
                        file_path = assets_dir / "files" / file_name
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, 'wb') as f:
                            f.write(base64.b64decode(encoded))
                        relative_path = files_location_prefix + str(file_path.relative_to(assets_dir.parent))
                        a_tag['href'] = relative_path
                        downloaded_files[href] = str(file_path)
                    except Exception as e:
                        logger.error(f"Failed to process data URI: {e}")
            elif parsed_url.path.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
                # Handle regular file URL
                if not href.startswith(('http', '//')):
                    href = urljoin(base_url, href)
                if downloader:
                    saved_path = await downloader.download(href, assets_dir / "files", asset_type='document')
                    if saved_path:
                        relative_path = files_location_prefix + str(saved_path.relative_to(assets_dir.parent))
                        a_tag['href'] = relative_path
                        downloaded_files[href] = str(saved_path)
        return soup, {'downloaded_files': downloaded_files}


class TaskInfoProcessor:
    """
    Processor for extracting and preserving task metadata panels.

    This processor finds and preserves the 'task-header-panel' divs that
    contain official metadata such as KES codes, answer type, etc.
    It ensures these panels remain in the processed output.
    """

    def process(
        self, soup: BeautifulSoup, assets_dir: Path, **kwargs
    ) -> Tuple[BeautifulSoup, Dict]:
        """
        Process a BeautifulSoup object to preserve task metadata panels.

        Args:
            soup (BeautifulSoup): Parsed HTML content to process.
            assets_dir (Path): Directory for assets (not used in this processor).
            **kwargs: Additional arguments (not used in this processor).

        Returns:
            Tuple[BeautifulSoup, Dict]:
                - Modified soup (unchanged in this processor)
                - Empty metadata dictionary
        """
        logger.debug("Starting TaskInfoProcessor...")
        # This processor currently doesn't modify the soup, just ensures task-header-panel is preserved
        return soup, {}


class InputFieldRemover:
    """
    Processor for removing interactive form elements.

    This processor removes input fields, textareas, and other interactive
    elements that are not needed in the static representation of problems.
    """

    def process(
        self, soup: BeautifulSoup, assets_dir: Path, **kwargs
    ) -> Tuple[BeautifulSoup, Dict]:
        """
        Process a BeautifulSoup object to remove input fields.

        Args:
            soup (BeautifulSoup): Parsed HTML content to process.
            assets_dir (Path): Directory for assets (not used in this processor).
            **kwargs: Additional arguments (not used in this processor).

        Returns:
            Tuple[BeautifulSoup, Dict]:
                - Modified soup with input fields removed
                - Empty metadata dictionary
        """
        logger.debug("Starting InputFieldRemover...")
        for input_tag in soup.find_all(['input', 'textarea', 'button', 'select']):
            input_tag.decompose()
        return soup, {}


class MathMLRemover:
    """
    Processor for removing or replacing MathML content.

    This processor handles MathML elements by either removing them completely
    or replacing them with placeholder text, depending on configuration.
    """

    def process(
        self, soup: BeautifulSoup, assets_dir: Path, **kwargs
    ) -> Tuple[BeautifulSoup, Dict]:
        """
        Process a BeautifulSoup object to handle MathML content.

        Args:
            soup (BeautifulSoup): Parsed HTML content to process.
            assets_dir (Path): Directory for assets (not used in this processor).
            **kwargs: Additional arguments (not used in this processor).

        Returns:
            Tuple[BeautifulSoup, Dict]:
                - Modified soup with MathML handled
                - Empty metadata dictionary
        """
        logger.debug("Starting MathMLRemover...")
        for math_tag in soup.find_all('math'):
            math_tag.decompose()
        return soup, {}


class UnwantedElementRemover:
    """
    Processor for removing miscellaneous unwanted elements.

    This processor removes elements such as scripts, styles, and other
    content that does not contribute to the core problem statement.
    """

    def process(
        self, soup: BeautifulSoup, assets_dir: Path, **kwargs
    ) -> Tuple[BeautifulSoup, Dict]:
        """
        Process a BeautifulSoup object to remove unwanted elements.

        Args:
            soup (BeautifulSoup): Parsed HTML content to process.
            assets_dir (Path): Directory for assets (not used in this processor).
            **kwargs: Additional arguments (not used in this processor).

        Returns:
            Tuple[BeautifulSoup, Dict]:
                - Modified soup with unwanted elements removed
                - Empty metadata dictionary
        """
        logger.debug("Starting UnwantedElementRemover...")
        for script in soup.find_all('script'):
            script.decompose()
        for style in soup.find_all('style'):
            style.decompose()
        for div in soup.find_all('div', class_=lambda x: x and 'unwanted' in x.lower()):
            div.decompose()
        return soup, {}
