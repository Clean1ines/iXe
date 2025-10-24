import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin


logger = logging.getLogger(__name__)


class AssetDownloader:
    """A class to handle downloading assets from web pages.

    Attributes:
        page: A Playwright page object for making HTTP requests.
        base_url: The base URL used to resolve relative asset URLs.
        files_location_prefix: Prefix to append to asset paths when constructing URLs.
    """

    def __init__(self, page: 'playwright.sync_api.Page', base_url: str, files_location_prefix: str = '../../'):
        """Initializes the AssetDownloader with necessary configuration.

        Args:
            page: Playwright page instance for HTTP requests.
            base_url: Base URL for resolving relative asset paths.
            files_location_prefix: URL prefix to prepend to asset paths.
        """
        self.page = page
        self.base_url = base_url
        self.files_location_prefix = files_location_prefix
        logger.debug(f"AssetDownloader initialized with base_url: {base_url}, prefix: {files_location_prefix}")

    def download(self, asset_src: str, save_dir: Path, asset_type: str = 'image') -> Optional[Path]:
        """Downloads an asset from the web and saves it locally.

        Args:
            asset_src: Relative path or URL of the asset.
            save_dir: Directory where the asset will be saved.
            asset_type: Type of asset (e.g., 'image', 'script') for logging.

        Returns:
            Path to the saved file if successful, None otherwise.
        """
        logger.info(f"Attempting to download {asset_type}: {asset_src} to {save_dir}")
        
        # Construct the full URL - urljoin will normalize the path
        logger.debug(f"Constructing full asset path using prefix '{self.files_location_prefix}' and src '{asset_src}'")
        full_asset_path = self.files_location_prefix + asset_src
        
        logger.debug(f"Constructing full URL from base '{self.base_url}' and path '{full_asset_path}'")
        asset_url = urljoin(self.base_url, full_asset_path)

        try:
            logger.debug(f"Initiating GET request to: {asset_url}")
            response = self.page.request.get(asset_url)
            
            if response.ok:
                logger.debug(f"Download request for {asset_src} successful, status: {response.status}")
                save_filename = Path(asset_src).name
                save_path = save_dir / save_filename
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(response.body())
                logger.info(f"Successfully downloaded {asset_type} from {asset_src} and saved to {save_path}")
                logger.debug(f"Returning save path: {save_path}")
                return save_path
            else:
                logger.warning(f"Failed to download {asset_type} {asset_url}. Status: {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error downloading {asset_type} {asset_url}: {e}", exc_info=True)
            return None
