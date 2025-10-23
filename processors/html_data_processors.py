"""
Module for processing HTML data and extracting content.

This module provides various processors for handling different aspects of HTML content
including images, file links, task information, input fields, and MathML elements.
"""

import re
from pathlib import Path
from typing import Dict, Tuple, Optional
from bs4 import BeautifulSoup
from utils.downloader import AssetDownloader


class ImageScriptProcessor:
    """
    A class to process image-related scripts in HTML content.

    This processor finds scripts containing ShowPicture function calls,
    downloads the referenced images, and replaces the scripts with img tags.
    """

    def __init__(self, downloader: AssetDownloader):
        """
        Initializes the ImageScriptProcessor.

        Args:
            downloader (AssetDownloader): An instance of AssetDownloader
                                         for downloading image assets.
        """
        self.downloader = downloader

    def process(self, soup: BeautifulSoup, run_folder_page: Path) -> Tuple[BeautifulSoup, Dict[str, str]]:
        """
        Processes script tags containing ShowPicture calls and replaces them with img tags.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.
            run_folder_page (Path): The folder where the HTML page will be saved.
                                   Used for calculating relative paths for images.

        Returns:
            Tuple[BeautifulSoup, Dict[str, str]]: A tuple containing:
                - Updated BeautifulSoup object with scripts replaced by img tags
                - Dictionary mapping original image sources to local relative paths
        """
        downloaded_images = {}
        pattern = re.compile(r'ShowPicture\w*\s*\(\s*[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
        
        for script_tag in soup.find_all('script', string=pattern):
            script_text = script_tag.get_text()
            match = pattern.search(script_text)
            
            if match:
                img_src = match.group(1)
                assets_dir = run_folder_page / "assets"
                local_path = self.downloader.download(img_src, assets_dir, asset_type='image')
                
                if local_path:
                    # Calculate path relative to the HTML file's directory
                    path_relative_to_html = str(local_path.relative_to(run_folder_page))
                    
                    # Create new img tag
                    new_img = soup.new_tag('img', src=path_relative_to_html)
                    script_tag.replace_with(new_img)
                    
                    downloaded_images[img_src] = path_relative_to_html
        
        return soup, downloaded_images


class FileLinkProcessor:
    """
    A class to process file download links in HTML content.

    This processor finds file links (both JavaScript window.open calls and direct links),
    downloads the referenced files, and updates the links to point to local copies.
    """

    def __init__(self, downloader: AssetDownloader):
        """
        Initializes the FileLinkProcessor.

        Args:
            downloader (AssetDownloader): An instance of AssetDownloader
                                         for downloading file assets.
        """
        self.downloader = downloader

    def process(self, soup: BeautifulSoup, run_folder_page: Path) -> Tuple[BeautifulSoup, Dict[str, str]]:
        """
        Processes file download links and downloads the referenced files.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.
            run_folder_page (Path): The folder where the HTML page will be saved.
                                   Used for calculating relative paths for files.

        Returns:
            Tuple[BeautifulSoup, Dict[str, str]]: A tuple containing:
                - Updated BeautifulSoup object with file links pointing to local copies
                - Dictionary mapping original file URLs to local relative paths
        """
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
                assets_dir = run_folder_page / "assets"
                local_path = self.downloader.download(file_path, assets_dir, asset_type='file')
                
                if local_path:
                    # Calculate path relative to the HTML file's directory
                    path_relative_to_html = str(local_path.relative_to(run_folder_page))
                    
                    # Update the href to point to local file
                    a_tag['href'] = path_relative_to_html
                    downloaded_files[file_path] = path_relative_to_html
        
        return soup, downloaded_files


class TaskInfoProcessor:
    """
    A class to process task information buttons in HTML content.

    This processor updates the onclick handlers for info buttons to work
    in standalone HTML files.
    """

    def __init__(self):
        """Initializes the TaskInfoProcessor."""
        pass

    def process(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Updates info button onclick handlers for standalone HTML compatibility.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.

        Returns:
            BeautifulSoup: Updated BeautifulSoup object with modified info buttons
        """
        for info_button in soup.find_all('div', class_='info-button'):
            info_button['onclick'] = "toggleInfo(this); return false;"
        
        return soup


class InputFieldRemover:
    """
    A class to remove answer input fields from HTML content.

    This processor removes the original FIPI answer input fields that are
    not needed in the processed output.
    """

    def __init__(self):
        """Initializes the InputFieldRemover."""
        pass

    def process(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Removes answer input fields from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.

        Returns:
            BeautifulSoup: Updated BeautifulSoup object without answer input fields
        """
        for input_tag in soup.find_all('input', attrs={'name': 'answer'}):
            input_tag.decompose()
        
        return soup


class MathMLRemover:
    """
    A class to remove MathML elements from HTML content.

    This processor removes MathML tags to allow proper rendering with MathJax
    or other math rendering libraries.
    """

    def __init__(self):
        """Initializes the MathMLRemover."""
        pass

    def process(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Removes MathML elements from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing HTML to process.

        Returns:
            BeautifulSoup: Updated BeautifulSoup object without MathML elements
        """
        for math_tag in soup.find_all(['math', 'mml:math']):
            math_tag.decompose()
        
        return soup