"""
Tests for html_data_processors module.
"""

import unittest
from pathlib import Path
from io import StringIO
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from processors.html_data_processors import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover
)


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


class TestFileLinkProcessor(unittest.TestCase):
    """Test cases for FileLinkProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_downloader = MagicMock()
        self.processor = FileLinkProcessor(self.mock_downloader)

    def test_process_javascript_link(self):
        """Test processing JavaScript window.open links."""
        html_content = """
        <html>
            <body>
                <a href="javascript:var wnd=window.open('../../docs/test.zip','_blank')">Download ZIP</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        run_folder_page = Path('/fake/path/page1')
        
        # Configure mock to return a path
        expected_local_path = run_folder_page / "assets" / "test.zip"
        self.mock_downloader.download.return_value = expected_local_path
        
        # Process the soup
        updated_soup, downloaded_files = self.processor.process(soup, run_folder_page)
        
        # Verify downloader was called correctly
        self.mock_downloader.download.assert_called_once_with(
            'docs/test.zip', run_folder_page / "assets", asset_type='file'
        )
        
        # Verify link was updated
        links = updated_soup.find_all('a')
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['href'], 'assets/test.zip')
        
        # Verify downloaded_files dictionary
        self.assertEqual(downloaded_files, {'docs/test.zip': 'assets/test.zip'})

    def test_process_direct_link(self):
        """Test processing direct file links."""
        html_content = """
        <html>
            <body>
                <a href="../../files/document.pdf">Download PDF</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        run_folder_page = Path('/fake/path/page1')
        
        # Configure mock to return a path
        expected_local_path = run_folder_page / "assets" / "document.pdf"
        self.mock_downloader.download.return_value = expected_local_path
        
        # Process the soup
        updated_soup, downloaded_files = self.processor.process(soup, run_folder_page)
        
        # Verify downloader was called correctly
        self.mock_downloader.download.assert_called_once_with(
            'files/document.pdf', run_folder_page / "assets", asset_type='file'
        )
        
        # Verify link was updated
        links = updated_soup.find_all('a')
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['href'], 'assets/document.pdf')
        
        # Verify downloaded_files dictionary
        self.assertEqual(downloaded_files, {'files/document.pdf': 'assets/document.pdf'})

    def test_process_no_file_links(self):
        """Test processing when no file links are found."""
        html_content = """
        <html>
            <body>
                <a href="page.html">Regular link</a>
                <a href="javascript:alert('Hello')">JavaScript alert</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        original_html = str(soup)
        run_folder_page = Path('/fake/path/page1')
        
        # Process the soup
        updated_soup, downloaded_files = self.processor.process(soup, run_folder_page)
        
        # Verify downloader was not called
        self.mock_downloader.download.assert_not_called()
        
        # Verify soup is unchanged
        self.assertEqual(str(updated_soup), original_html)
        
        # Verify downloaded_files is empty
        self.assertEqual(downloaded_files, {})

    def test_process_download_failure(self):
        """Test processing when file download fails."""
        html_content = """
        <html>
            <body>
                <a href="../../files/test.zip">Download ZIP</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        original_html = str(soup)
        run_folder_page = Path('/fake/path/page1')
        
        # Configure mock to return None (download failure)
        self.mock_downloader.download.return_value = None
        
        # Process the soup
        updated_soup, downloaded_files = self.processor.process(soup, run_folder_page)
        
        # Verify downloader was called
        self.mock_downloader.download.assert_called_once_with(
            'files/test.zip', run_folder_page / "assets", asset_type='file'
        )
        
        # Verify link was not updated
        links = updated_soup.find_all('a')
        self.assertEqual(links[0]['href'], '../../files/test.zip')
        
        # Verify downloaded_files is empty
        self.assertEqual(downloaded_files, {})


class TestTaskInfoProcessor(unittest.TestCase):
    """Test cases for TaskInfoProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = TaskInfoProcessor()

    def test_process_info_buttons(self):
        """Test processing info buttons."""
        html_content = """
        <html>
            <body>
                <div class="info-button" onclick="someOriginalFunction()">Info 1</div>
                <div class="info-button" onclick="anotherFunction()">Info 2</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Process the soup
        updated_soup = self.processor.process(soup)
        
        # Verify info buttons were updated
        info_buttons = updated_soup.find_all('div', class_='info-button')
        self.assertEqual(len(info_buttons), 2)
        
        for button in info_buttons:
            self.assertEqual(button['onclick'], "toggleInfo(this); return false;")

    def test_process_no_info_buttons(self):
        """Test processing when no info buttons are found."""
        html_content = """
        <html>
            <body>
                <div class="other-class">Some content</div>
                <button>Regular button</button>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        original_html = str(soup)
        
        # Process the soup
        updated_soup = self.processor.process(soup)
        
        # Verify soup is unchanged
        self.assertEqual(str(updated_soup), original_html)


class TestInputFieldRemover(unittest.TestCase):
    """Test cases for InputFieldRemover class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = InputFieldRemover()

    def test_remove_answer_inputs(self):
        """Test removing answer input fields."""
        html_content = """
        <html>
            <body>
                <input name="answer" value="test">
                <input type="text" name="answer">
                <input name="other" value="should remain">
                <div>Some content</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Process the soup
        updated_soup = self.processor.process(soup)
        
        # Verify answer inputs were removed
        answer_inputs = updated_soup.find_all('input', attrs={'name': 'answer'})
        self.assertEqual(len(answer_inputs), 0)
        
        # Verify other inputs remain
        other_inputs = updated_soup.find_all('input', attrs={'name': 'other'})
        self.assertEqual(len(other_inputs), 1)

    def test_no_answer_inputs(self):
        """Test processing when no answer inputs are found."""
        html_content = """
        <html>
            <body>
                <input name="username">
                <input name="password">
                <div>Some content</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        original_html = str(soup)
        
        # Process the soup
        updated_soup = self.processor.process(soup)
        
        # Verify soup is unchanged
        self.assertEqual(str(updated_soup), original_html)


class TestMathMLRemover(unittest.TestCase):
    """Test cases for MathMLRemover class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = MathMLRemover()

    def test_remove_math_tags(self):
        """Test removing math and mml:math tags."""
        html_content = """
        <html>
            <body>
                <math>Math content 1</math>
                <mml:math>MathML content</mml:math>
                <div>Regular content</div>
                <math>Math content 2</math>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Process the soup
        updated_soup = self.processor.process(soup)
        
        # Verify math tags were removed
        math_tags = updated_soup.find_all(['math', 'mml:math'])
        self.assertEqual(len(math_tags), 0)
        
        # Verify regular content remains
        divs = updated_soup.find_all('div')
        self.assertEqual(len(divs), 1)
        self.assertEqual(divs[0].get_text(), 'Regular content')

    def test_no_math_tags(self):
        """Test processing when no math tags are found."""
        html_content = """
        <html>
            <body>
                <div>Regular content 1</div>
                <span>Regular content 2</span>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        original_html = str(soup)
        
        # Process the soup
        updated_soup = self.processor.process(soup)
        
        # Verify soup is unchanged
        self.assertEqual(str(updated_soup), original_html)


if __name__ == '__main__':
    unittest.main()