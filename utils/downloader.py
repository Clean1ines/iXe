import logging
from pathlib import Path
from typing import Optional
import asyncio
import re
from playwright.async_api import Error as PlaywrightError

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
            response = await self.page.request.get(asset_url, ignore_https_errors=True)
            if response.ok:
                logger.debug(f"Download request for {asset_url} successful, status: {response.status}")
                save_filename = Path(asset_url).name
                # Очищаем имя файла от недопустимых символов
                save_filename = re.sub(r'[<>:"/\\|?*]', '_', save_filename)
                if not save_filename:
                    save_filename = f"asset_{hash(asset_url) % 1000000}"
                    
                save_path = save_dir / save_filename
                save_path.parent.mkdir(parents=True, exist_ok=True)
                content = await response.body()
                save_path.write_bytes(content)
                logger.info(f"Successfully downloaded {asset_type} from {asset_url} and saved to {save_path}")
                logger.debug(f"Returning save path: {save_path}")
                return save_path
            else:
                logger.warning(f"Failed to download {asset_type} {asset_url}. Status: {response.status}")
                return None
        except PlaywrightError as e:
            if "unable to verify the first certificate" in str(e):
                logger.warning(f"SSL certificate error for {asset_url}, trying alternative approach")
                return await self._download_with_alternative_method(asset_url, save_dir, asset_type)
            else:
                logger.error(f"Playwright error downloading {asset_type} {asset_url}: {e}", exc_info=True)
                return None
        except Exception as e:
            logger.error(f"Error downloading {asset_type} {asset_url}: {e}", exc_info=True)
            return None

    async def _download_with_alternative_method(self, asset_url: str, save_dir: Path, asset_type: str) -> Optional[Path]:
        """Альтернативный метод скачивания при проблемах с SSL"""
        try:
            import aiohttp
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(asset_url, timeout=30) as response:
                    if response.status == 200:
                        save_filename = Path(asset_url).name
                        save_filename = re.sub(r'[<>:"/\\|?*]', '_', save_filename)
                        if not save_filename:
                            save_filename = f"asset_{hash(asset_url) % 1000000}"
                            
                        save_path = save_dir / save_filename
                        save_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        content = await response.read()
                        save_path.write_bytes(content)
                        logger.info(f"Successfully downloaded {asset_type} using alternative method: {asset_url}")
                        return save_path
            return None
        except Exception as e:
            logger.error(f"Alternative download method failed for {asset_url}: {e}")
            return None

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
            response = await self.page.request.get(asset_url, ignore_https_errors=True)
            if response.ok:
                logger.debug(f"Download request for {asset_url} successful, status: {response.status}")
                content_bytes = await response.body()
                logger.info(f"Successfully downloaded bytes for asset {asset_url}, size: {len(content_bytes)}")
                return content_bytes
            else:
                logger.warning(f"Failed to download bytes for asset {asset_url}. Status: {response.status}")
                return None
        except PlaywrightError as e:
            if "unable to verify the first certificate" in str(e):
                logger.warning(f"SSL certificate error for bytes download {asset_url}")
                return None
            else:
                logger.error(f"Playwright error downloading bytes for asset {asset_url}: {e}", exc_info=True)
                return None
        except Exception as e:
            logger.error(f"Error downloading bytes for asset {asset_url}: {e}", exc_info=True)
            return None
