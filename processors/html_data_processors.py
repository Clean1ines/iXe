"""
Module for processing HTML data and extracting content.

This module provides the ImageScriptProcessor class which handles
replacement of image-related scripts with actual img tags.
"""

import re
from pathlib import Path
from typing import Dict, Tuple
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