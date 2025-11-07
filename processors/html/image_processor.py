import re
import logging
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from utils.downloader import AssetDownloader
from processors.html_processor_interface import IHTMLProcessor

logger = logging.getLogger(__name__)

class ImageScriptProcessor(IHTMLProcessor):
    """
    Processes image-related scripts and direct img tags, downloading images and updating src attributes.
    """
    async def process(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Processes ShowPicture scripts and direct <img> tags.

        Args:
            content: Input HTML content as string
            context: Processing context with additional parameters
                - 'run_folder_page': Path to the page's run folder
                - 'downloader': AssetDownloader instance to use for downloading
                - 'base_url': Base URL for constructing full image URLs
                - 'files_location_prefix': Prefix for file paths in HTML

        Returns:
            Tuple of processed HTML content and metadata dict containing downloaded images.
        """
        run_folder_page = context.get('run_folder_page')
        downloader = context.get('downloader')
        base_url = context.get('base_url', '')
        files_location_prefix = context.get('files_location_prefix', '')
        
        if downloader is None:
            raise ValueError("AssetDownloader must be provided in context")
        
        soup = BeautifulSoup(content, 'html.parser')
        assets_dir = run_folder_page / "assets"
        downloaded_files = {}
        downloaded_images = {}
        
        # Process ShowPicture scripts
        for script in soup.find_all('script', string=re.compile(r"ShowPicture$$'[^']*'$$")):
            match = re.search(r"ShowPicture$$'([^']*)'$$", script.string)
            if match:
                img_url = match.group(1)
                try:
                    local_path = await downloader.download(img_url, assets_dir, asset_type='image')
                    if local_path:
                        img_tag = soup.new_tag('img', src=f"assets/{local_path.name}")
                        script.replace_with(img_tag)
                        downloaded_images[img_url] = f"assets/{local_path.name}"
                        logger.info(f"Downloaded and replaced ShowPicture image: {img_url} -> assets/{local_path.name}")
                    else:
                        logger.warning(f"Failed to download image from ShowPicture script: {img_url}")
                except Exception as e:
                    logger.error(f"Error downloading image from ShowPicture script {img_url}: {e}")
        
        # Process direct <img> tags
        for img_tag in soup.find_all('img', src=True):
            img_src = img_tag['src']
            # Skip if already processed (e.g., already points to local assets/)
            if img_src.startswith('assets/'):
                logger.debug(f"Skipping already processed image: {img_src}")
                continue
            
            # Construct full URL if img_src is relative
            full_img_url = urljoin(base_url, img_src) if base_url else img_src
            
            try:
                local_path = await downloader.download(full_img_url, assets_dir, asset_type='image')
                if local_path:
                    # Use the correct path structure: assets/filename.ext
                    relative_path = f"assets/{local_path.name}"
                    img_tag['src'] = relative_path
                    downloaded_images[full_img_url] = relative_path
                    logger.info(f"Downloaded and updated img tag: {full_img_url} -> {relative_path}")
                else:
                    logger.warning(f"Failed to download image from img tag: {full_img_url}")
            except Exception as e:
                logger.error(f"Error downloading image from img tag {img_url}: {e}")
        
        return str(soup), {'downloaded_files': downloaded_files, 'downloaded_images': downloaded_images}
