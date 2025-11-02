import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from utils.downloader import AssetDownloader


class TestAssetDownloader(unittest.TestCase):
    def setUp(self):
        self.page = MagicMock()
        self.page.request = MagicMock()
        self.base_url = "https://example.com/"
        self.files_location_prefix = "../../"
        self.downloader = AssetDownloader(self.page, self.base_url, self.files_location_prefix)

    def test_download_success(self):
        # Mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.body.return_value = b"fake image data"
        self.page.request.get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_dir = Path(tmp_dir)
            result = self.await downloader.download("images/test.jpg", save_dir, "image")

            # Check if request was made with correct URL
            # urljoin normalizes the path, removing the ../..
            expected_url = "https://example.com/images/test.jpg"
            self.page.request.get.assert_called_once_with(expected_url)

            # Check if file was created
            expected_path = save_dir / "test.jpg"
            self.assertTrue(expected_path.exists())
            self.assertEqual(result, expected_path)
            self.assertEqual(b"fake image data", expected_path.read_bytes())

    def test_download_failure_status(self):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 404
        self.page.request.get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.await downloader.download("images/missing.jpg", Path(tmp_dir))

        self.assertIsNone(result)

    def test_download_exception(self):
        self.page.request.get.side_effect = Exception("Network error")

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.await downloader.download("images/test.jpg", Path(tmp_dir))

        self.assertIsNone(result)

    def test_download_with_different_base_url(self):
        """Test with a base URL that has a path component"""
        downloader = AssetDownloader(
            self.page, 
            "https://example.com/some/path/", 
            "../../assets/"
        )
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.body.return_value = b"test data"
        self.page.request.get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = await downloader.download("image.jpg", Path(tmp_dir))
            
            # The URL should be normalized by urljoin
            expected_url = "https://example.com/assets/image.jpg"
            self.page.request.get.assert_called_once_with(expected_url)


if __name__ == "__main__":
    unittest.main()