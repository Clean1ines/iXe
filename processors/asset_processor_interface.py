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


class AssetProcessor(abc.ABC):
    """Abstract base class defining the interface for asset processors.

    All concrete asset processors (e.g., ImageScriptProcessor, FileLinkProcessor)
    must inherit from this class and implement the `process` method.

    This interface enables polymorphic usage of processors and simplifies
    dependency injection and unit testing.
    """

    @abc.abstractmethod
    def process(self, soup: BeautifulSoup, assets_dir: Path, **kwargs) -> Tuple[BeautifulSoup, Dict[str, Any]]:
        """Process the BeautifulSoup object, potentially downloading or transforming assets.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object representing the HTML fragment to process.
            assets_dir (Path): The directory where downloaded assets should be saved.
                               Relative paths in the returned metadata should be relative to
                               the parent of this directory (i.e., the HTML page directory).
            **kwargs: Additional keyword arguments that may be required by specific implementations.
                      Common examples include:
                      - `downloader`: An instance of `AssetDownloader` for downloading assets.
                      - `run_folder_page`: The directory containing the HTML page (alternative to `assets_dir.parent`).

        Returns:
            Tuple[BeautifulSoup, Dict[str, Any]]: A tuple containing:
                - The (potentially modified) BeautifulSoup object after processing.
                - A dictionary of metadata describing changes made, typically mapping original
                  asset identifiers (e.g., URLs) to local relative paths or other relevant info.
                  Example: {"original_image_url.jpg": "assets/image.jpg"}.
        """
        pass
