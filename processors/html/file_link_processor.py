import re
import logging
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from bs4.element import Tag
from utils.downloader import AssetDownloader
from domain.interfaces.html_processor import IHTMLProcessor

logger = logging.getLogger(__name__)

class FileLinkProcessor(IHTMLProcessor):
    """
    Processes file links, downloading files and updating href attributes.
    """
    
    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str,
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and return structured data.
        This method processes file links in the qblock content.
        """
        # Process the qblock content to handle file links
        qblock_content = str(qblock)
        
        # Extract context parameters from kwargs
        run_folder_page = kwargs.get('run_folder_page')
        downloader = kwargs.get('downloader')
        files_location_prefix = kwargs.get('files_location_prefix', '')
        
        if downloader is None:
            raise ValueError("AssetDownloader must be provided in context")
        
        soup = BeautifulSoup(qblock_content, 'html.parser')
        assets_dir = run_folder_page / "assets" if run_folder_page else Path("assets")
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
        
        # Update the qblock with processed content
        processed_qblock = soup.find('div', class_='qblock') or soup.find('div')
        
        # Return the processed block data
        return {
            'header_container': header_container,
            'qblock': processed_qblock,
            'block_index': block_index,
            'subject': subject,
            'base_url': base_url
        }

    async def process(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Processes javascript file links and direct file links.

        Args:
            content: Input HTML content as string
            context: Processing context with additional parameters
                - 'run_folder_page': Path to the page's run folder
                - 'downloader': AssetDownloader instance to use for downloading
                - 'base_url': Base URL for constructing full file URLs
                - 'files_location_prefix': Prefix for file paths in HTML

        Returns:
            Tuple of processed HTML content and metadata dict containing downloaded files.
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
        
        return str(soup), {'downloaded_files': downloaded_files, 'downloaded_images': downloaded_images}
