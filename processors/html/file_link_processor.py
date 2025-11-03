import re
import logging
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from utils.downloader import AssetDownloader

logger = logging.getLogger(__name__)

class FileLinkProcessor:
    """
    Processes file links, downloading files and updating href attributes.
    """
    async def process(self, soup: BeautifulSoup, run_folder_page: Path, downloader: AssetDownloader = None, base_url: str = "", files_location_prefix: str = ""):
        """
        Processes javascript file links and direct file links.

        Args:
            soup: BeautifulSoup object representing the page content.
            run_folder_page: Path to the page's run folder.
            downloader: AssetDownloader instance to use for downloading.
            base_url: Base URL for constructing full file URLs.
            files_location_prefix: Prefix for file paths in HTML.

        Returns:
            Tuple of modified soup and metadata dict containing downloaded files.
        """
        if downloader is None:
            raise ValueError("AssetDownloader must be provided")
        assets_dir = run_folder_page / "assets"
        downloaded_files = {}
        downloaded_images = {}
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('javascript:'):
                match = re.search(r"window\.open$$'([^']*)'", href)
                if match:
                    file_url = match.group(1).lstrip('../')
                    # Construct full URL if file_url is relative and base_url is provided
                    full_file_url = urljoin(base_url, file_url) if base_url else file_url
                    try:
                        local_path = await downloader.download(full_file_url, assets_dir, asset_type='file')
                        if local_path:
                            a['href'] = f"assets/{local_path.name}"
                            downloaded_images[full_file_url] = f"assets/{local_path.name}"
                    except Exception as e:
                        logger.error(f"Error downloading file from javascript link {full_file_url}: {e}")
            elif href.endswith(('.pdf', '.zip', '.doc', '.docx')):
                file_url = href.lstrip('../')
                # Construct full URL if file_url is relative and base_url is provided
                full_file_url = urljoin(base_url, file_url) if base_url else file_url
                try:
                    local_path = await downloader.download(full_file_url, assets_dir, asset_type='file')
                    if local_path:
                        a['href'] = f"assets/{local_path.name}"
                        downloaded_images[full_file_url] = f"assets/{local_path.name}"
                except Exception as e:
                    logger.error(f"Error downloading file from direct link {full_file_url}: {e}")
        return soup, {'downloaded_files': downloaded_files, 'downloaded_images': downloaded_images}
