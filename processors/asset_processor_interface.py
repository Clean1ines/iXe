"""
Module defining the abstract interface for HTML asset processors.

This module provides the `AssetProcessor` abstract base class that serves as a
contract for all classes responsible for processing parts of HTML content,
such as downloading and replacing assets, removing elements, or transforming markup.
"""
import abc
from pathlib import Path
from typing import Any, Dict, Tuple
from bs4 import BeautifulSoup
from domain.interfaces.html_processor import IHTMLProcessor


class AssetProcessor(IHTMLProcessor, abc.ABC):
    """Abstract base class defining the interface for asset processors.

    All concrete asset processors (e.g., ImageScriptProcessor, FileLinkProcessor)
    must inherit from this class and implement the `process` method.

    This interface enables polymorphic usage of processors and simplifies
    dependency injection and unit testing.
    """

    @abc.abstractmethod
    def process(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Process the HTML content string, potentially downloading or transforming assets.

        Args:
            content (str): The HTML content string to process.
            context (Dict[str, Any]): A dictionary containing processing context.
                      Common examples include:
                      - `run_folder_page`: The directory containing the HTML page.
                      - `downloader`: An instance of `AssetDownloader` for downloading assets.
                      - `base_url`: Base URL for constructing full file URLs.
                      - `files_location_prefix`: Prefix for file paths in HTML.

        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - The (potentially modified) HTML content string after processing.
                - A dictionary of metadata describing changes made, typically mapping original
                  asset identifiers (e.g., URLs) to local relative paths or other relevant info.
                  Example: {"original_image_url.jpg": "assets/image.jpg"}.
        """
        pass
