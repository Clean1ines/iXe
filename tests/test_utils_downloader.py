import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from utils.downloader import AssetDownloader


class TestAssetDownloader:
    def setup_method(self):
        self.page = MagicMock()
        self.page.request = MagicMock()
        self.downloader = AssetDownloader(self.page)

    @pytest.mark.asyncio
    async def test_download_success(self):
        # Mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.body.return_value = b"fake image data"
        self.page.request.get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_dir = Path(tmp_dir)
            result = await self.downloader.download("https://example.com/images/test.jpg", save_dir, "image")

            # Check if request was made with correct URL
            self.page.request.get.assert_called_once_with("https://example.com/images/test.jpg")

            # Check if file was created
            expected_path = save_dir / "test.jpg"
            assert expected_path.exists()
            assert result == expected_path
            assert b"fake image data" == expected_path.read_bytes()

    @pytest.mark.asyncio
    async def test_download_failure_status(self):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 404
        self.page.request.get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = await self.downloader.download("https://example.com/images/missing.jpg", Path(tmp_dir))

        assert result is None

    @pytest.mark.asyncio
    async def test_download_exception(self):
        self.page.request.get.side_effect = Exception("Network error")

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = await self.downloader.download("https://example.com/images/test.jpg", Path(tmp_dir))

        assert result is None

    @pytest.mark.asyncio
    async def test_download_bytes_success(self):
        """Test the download_bytes method."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.body.return_value = b"test data bytes"
        self.page.request.get.return_value = mock_response

        result = await self.downloader.download_bytes("https://example.com/data.bin")

        self.page.request.get.assert_called_once_with("https://example.com/data.bin")
        assert result == b"test data bytes"

    @pytest.mark.asyncio
    async def test_download_bytes_failure_status(self):
        """Test download_bytes with a failing status code."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 500
        self.page.request.get.return_value = mock_response

        result = await self.downloader.download_bytes("https://example.com/data.bin")

        assert result is None

    @pytest.mark.asyncio
    async def test_download_bytes_exception(self):
        """Test download_bytes when an exception occurs."""
        self.page.request.get.side_effect = Exception("Network error")

        result = await self.downloader.download_bytes("https://example.com/data.bin")

        assert result is None

if __name__ == "__main__":
    unittest.main()
