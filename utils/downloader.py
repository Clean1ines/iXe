from pathlib import Path
from typing import Optional
from urllib.parse import urljoin


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

    def download(self, asset_src: str, save_dir: Path, asset_type: str = 'image') -> Optional[Path]:
        """Downloads an asset from the web and saves it locally.

        Args:
            asset_src: Relative path or URL of the asset.
            save_dir: Directory where the asset will be saved.
            asset_type: Type of asset (e.g., 'image', 'script') for logging.

        Returns:
            Path to the saved file if successful, None otherwise.
        """
        # Construct the full URL - urljoin will normalize the path
        asset_path = self.files_location_prefix + asset_src
        full_url = urljoin(self.base_url, asset_path)

        try:
            response = self.page.request.get(full_url)
            if response.ok:
                save_filename = Path(asset_src).name
                save_path = save_dir / save_filename
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(response.body())
                print(f"Successfully downloaded {asset_type} to {save_path}")
                return save_path
            else:
                print(f"Error downloading {asset_type} {full_url}: Status {response.status}")
                return None
        except Exception as e:
            print(f"Error downloading {asset_type} {full_url}: {e}")
            return None