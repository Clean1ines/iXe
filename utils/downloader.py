# utils/downloader.py
import logging
from pathlib import Path
from typing import Optional
import asyncio
logger = logging.getLogger(__name__)

class AssetDownloader:
    """A class to handle downloading assets from web pages.
    Attributes:
        page: A Playwright page object for making HTTP requests.
    """
    def __init__(self, page: 'playwright.async_api.Page'):
        """Initializes the AssetDownloader with necessary configuration.
        Args:
            page: Playwright page instance for HTTP requests.
        """
        self.page = page
        logger.debug(f"AssetDownloader initialized with page: {page is not None}")

    async def download(self, asset_url: str, save_dir: Path, asset_type: str = 'image') -> Optional[Path]:
        """Downloads an asset from the web and saves it locally.
        Args:
            asset_url: Full URL of the asset to download.
            save_dir: Directory where the asset will be saved.
            asset_type: Type of asset (e.g., 'image', 'script') for logging.
        Returns:
            Path to the saved file if successful, None otherwise.
        """
        logger.info(f"Attempting to download {asset_type}: {asset_url} to {save_dir}")
        try:
            logger.debug(f"Initiating GET request to: {asset_url}")
            response = await self.page.request.get(asset_url) # Await the coroutine
            if response.ok:
                logger.debug(f"Download request for {asset_url} successful, status: {response.status}")
                save_filename = Path(asset_url).name
                save_path = save_dir / save_filename
                save_path.parent.mkdir(parents=True, exist_ok=True)
                content = await response.body() # Await the body coroutine
                save_path.write_bytes(content)
                logger.info(f"Successfully downloaded {asset_type} from {asset_url} and saved to {save_path}")
                logger.debug(f"Returning save path: {save_path}")
                return save_path
            else:
                logger.warning(f"Failed to download {asset_type} {asset_url}. Status: {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error downloading {asset_type} {asset_url}: {e}", exc_info=True)
            return None

    # NEW: Add the download_bytes method as expected by ImageScriptProcessor
    async def download_bytes(self, asset_url: str) -> Optional[bytes]:
        """Downloads an asset from the web and returns its content as bytes.
        Args:
            asset_url: Full URL of the asset to download.
        Returns:
            Bytes of the downloaded asset if successful, None otherwise.
        """
        logger.info(f"Attempting to download bytes for asset: {asset_url}")
        try:
            logger.debug(f"Initiating GET request to: {asset_url}")
            response = await self.page.request.get(asset_url) # Await the coroutine
            if response.ok:
                logger.debug(f"Download request for {asset_url} successful, status: {response.status}")
                content_bytes = await response.body() # Await the body coroutine
                logger.info(f"Successfully downloaded bytes for asset {asset_url}, size: {len(content_bytes)}")
                return content_bytes
            else:
                logger.warning(f"Failed to download bytes for asset {asset_url}. Status: {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error downloading bytes for asset {asset_url}: {e}", exc_info=True)
            return None
