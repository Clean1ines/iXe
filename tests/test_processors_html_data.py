"""
Tests for html_data_processors module.
"""

import unittest
from pathlib import Path
from io import StringIO
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from processors.html_data_processors import ImageScriptProcessor


class TestImageScriptProcessor(unittest.TestCase):
    """Test cases for ImageScriptProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_downloader = MagicMock()
        self.processor = ImageScriptProcessor(self.mock_downloader)

    def test_process_success(self):
        """Test successful processing and replacement of script tag."""
        # Create HTML with script tag
        html_content = """
        <html>
            <body>
                <script>ShowPicture('test.jpg')</script>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        run_folder_page = Path('/fake/path/page1')
        
        # Configure mock to return a path
        expected_local_path = run_folder_page / "assets" / "test.jpg"
        self.mock_downloader.download.return_value = expected_local_path
        
        # Process the soup
        updated_soup, downloaded_images = self.processor.process(soup, run_folder_page)
        
        # Verify downloader was called correctly
        self.mock_downloader.download.assert_called_once_with(
            'test.jpg', run_folder_page / "assets", asset_type='image'
        )
        
        # Verify script was replaced with img tag
        scripts = updated_soup.find_all('script', string=True)
        self.assertEqual(len(scripts), 0)
        
        imgs = updated_soup.find_all('img')
        self.assertEqual(len(imgs), 1)
        self.assertEqual(imgs[0]['src'], 'assets/test.jpg')
        
        # Verify downloaded_images dictionary
        self.assertEqual(downloaded_images, {'test.jpg': 'assets/test.jpg'})

    def test_process_no_match(self):
        """Test processing when no matching scripts are found."""
        # Create HTML without matching scripts
        html_content = """
        <html>
            <body>
                <script>SomeOtherFunction('test.jpg')</script>
                <div>Some content</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        original_html = str(soup)
        run_folder_page = Path('/fake/path/page1')
        
        # Process the soup
        updated_soup, downloaded_images = self.processor.process(soup, run_folder_page)
        
        # Verify downloader was not called
        self.mock_downloader.download.assert_not_called()
        
        # Verify soup is unchanged
        self.assertEqual(str(updated_soup), original_html)
        
        # Verify downloaded_images is empty
        self.assertEqual(downloaded_images, {})

    def test_process_download_failure(self):
        """Test processing when image download fails."""
        # Create HTML with script tag
        html_content = """
        <html>
            <body>
                <script>ShowPicture('test.jpg')</script>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        original_html = str(soup)
        run_folder_page = Path('/fake/path/page1')
        
        # Configure mock to return None (download failure)
        self.mock_downloader.download.return_value = None
        
        # Process the soup
        updated_soup, downloaded_images = self.processor.process(soup, run_folder_page)
        
        # Verify downloader was called
        self.mock_downloader.download.assert_called_once_with(
            'test.jpg', run_folder_page / "assets", asset_type='image'
        )
        
        # Verify script was not replaced
        self.assertEqual(str(updated_soup), original_html)
        
        # Verify downloaded_images is empty
        self.assertEqual(downloaded_images, {})


if __name__ == '__main__':
    unittest.main()