"""
Unit tests for the BlockProcessor class.
"""
import unittest
from unittest.mock import MagicMock, patch, create_autospec
from pathlib import Path
from bs4 import BeautifulSoup
from bs4.element import Tag

from processors.block_processor import BlockProcessor
from utils.downloader import AssetDownloader
from processors.html_data_processors import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover
)
from utils.metadata_extractor import MetadataExtractor
from models.problem_builder import ProblemBuilder
from models.problem_schema import Problem


class TestBlockProcessor(unittest.TestCase):
    """
    Test suite for the BlockProcessor class.
    """

    def setUp(self):
        """
        Set up the test case with mock dependencies and a BlockProcessor instance.
        """
        # Create mocks for dependencies
        self.mock_downloader_factory = MagicMock()
        self.mock_metadata_extractor = create_autospec(MetadataExtractor)
        self.mock_problem_builder = create_autospec(ProblemBuilder)

        # Create mock AssetProcessor instances
        self.mock_processors = [
            create_autospec(ImageScriptProcessor),
            create_autospec(FileLinkProcessor),
            create_autospec(TaskInfoProcessor),
            create_autospec(InputFieldRemover),
            create_autospec(MathMLRemover),
            create_autospec(UnwantedElementRemover),
        ]

        # Create the BlockProcessor instance under test
        self.block_processor = BlockProcessor(task_inferer=None, 
            asset_downloader_factory=self.mock_downloader_factory,
            processors=self.mock_processors,
            metadata_extractor=self.mock_metadata_extractor,
            problem_builder=self.mock_problem_builder,
        )

        # Create temporary directory for tests
        self.temp_dir = Path("/tmp/test_block_processor")  # Using a fixed path for simplicity in this mock test
        self.temp_dir.mkdir(exist_ok=True)

        # Create sample BeautifulSoup Tags for testing
        self.header_html = '<div class="header"><span class="canselect">1</span><span class="answer-button" onclick="checkButtonClick(\'form1\')">Button</span></div>'
        self.qblock_html = '<div class="qblock">Assignment text</div>'
        self.header_container = BeautifulSoup(self.header_html, 'html.parser').find('div')
        self.qblock = BeautifulSoup(self.qblock_html, 'html.parser').find('div')

    def tearDown(self):
        """
        Clean up temporary directory after tests.
        """
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_process_calls_dependencies_correctly(self):
        """
        Test that the process method calls all dependencies with correct arguments.
        """
        # Arrange
        block_index = 0
        page_num = "page_1"
        page_assets_dir = self.temp_dir / "assets"
        page_assets_dir.mkdir(exist_ok=True)
        proj_id = "proj_A"
        base_url = "https://example.com/fipi  "
        page_obj = MagicMock()

        # Mock return values for dependencies
        mock_downloader = MagicMock(spec=AssetDownloader)
        self.mock_downloader_factory.return_value = mock_downloader

        self.mock_metadata_extractor.extract.return_value = {"task_id": "1", "form_id": "form1"}

        # Mock processor returns (soup, metadata)
        # Create a mock soup that behaves like BeautifulSoup for the final processed result
        mock_final_soup = MagicMock(spec=BeautifulSoup)
        mock_final_soup.__str__.return_value = "<div class='qblock'>Processed Assignment text</div>"
        # Crucially, mock the get_text method to return a string
        mock_final_soup.get_text.return_value = "Processed Assignment text"

        for proc in self.mock_processors:
            # Each processor should return the mock soup (or a new one if it modifies it)
            # For simplicity, assume they return the same mock soup object for the final step
            proc.process.return_value = (mock_final_soup, {})

        mock_problem = MagicMock(spec=Problem)
        self.mock_problem_builder.build.return_value = mock_problem

        # Act
        result = self.block_processor.process(
            header_container=self.header_container,
            qblock=self.qblock,
            block_index=block_index,
            page_num=page_num,
            page_assets_dir=page_assets_dir,
            proj_id=proj_id,
            base_url=base_url,
            page=page_obj
        )

        # Assert
        # Check if downloader factory was called with correct arguments
        self.mock_downloader_factory.assert_called_once_with(page_obj, base_url, "../../")

        # Check if metadata extractor was called
        self.mock_metadata_extractor.extract.assert_called_once_with(self.header_container)

        # Check if processors were called
        for proc in self.mock_processors:
            proc.process.assert_called()

        # Check if problem builder was called
        self.mock_problem_builder.build.assert_called_once()

        # Check return tuple structure and types
        self.assertEqual(len(result), 6)
        self.assertIsInstance(result[0], str)  # processed_html_string
        self.assertIsInstance(result[1], str) # assignment_text - now correctly mocked
        self.assertIsInstance(result[2], dict) # new_images_dict
        self.assertIsInstance(result[3], dict) # new_files_dict
        self.assertIsInstance(result[4], Problem) # problem
        self.assertIsInstance(result[5], dict) # block_metadata

    def test_process_with_specific_processor_behavior(self):
        """
        Test that the process method handles specific processor outputs correctly.
        """
        # Arrange
        block_index = 0
        page_num = "page_1"
        page_assets_dir = self.temp_dir / "assets"
        page_assets_dir.mkdir(exist_ok=True)
        proj_id = "proj_A"
        base_url = "https://example.com/fipi  "
        page_obj = MagicMock()

        # Mock return values
        mock_downloader = MagicMock(spec=AssetDownloader)
        self.mock_downloader_factory.return_value = mock_downloader

        self.mock_metadata_extractor.extract.return_value = {"task_id": "2", "form_id": "form2"}

        # Mock a specific processor to return metadata
        # Create a mock soup that behaves like BeautifulSoup
        mock_final_soup = MagicMock(spec=BeautifulSoup)
        mock_final_soup.__str__.return_value = "<div class='qblock'>Processed Assignment text</div>"
        mock_final_soup.get_text.return_value = "Processed Assignment text"


        mock_image_proc = create_autospec(ImageScriptProcessor)
        mock_image_proc.process.return_value = (mock_final_soup, {"downloaded_images": {"src1": "local/path1"}})

        mock_file_proc = create_autospec(FileLinkProcessor)
        mock_file_proc.process.return_value = (mock_final_soup, {"downloaded_files": {"file1": "local/path2"}})

        # Mock other processors
        other_procs = [create_autospec(TaskInfoProcessor), create_autospec(InputFieldRemover), create_autospec(MathMLRemover), create_autospec(UnwantedElementRemover)]
        for proc in other_procs:
             proc.process.return_value = (mock_final_soup, {})

        self.mock_processors = [mock_image_proc, mock_file_proc] + other_procs
        self.block_processor.processors = self.mock_processors

        mock_problem = MagicMock(spec=Problem)
        self.mock_problem_builder.build.return_value = mock_problem

        # Act
        result = self.block_processor.process(
            header_container=self.header_container,
            qblock=self.qblock,
            block_index=block_index,
            page_num=page_num,
            page_assets_dir=page_assets_dir,
            proj_id=proj_id,
            base_url=base_url,
            page=page_obj
        )

        # Assert
        processed_html_string, assignment_text, new_images_dict, new_files_dict, problem, block_metadata = result

        # Verify that the returned metadata dicts contain the expected items from processors
        self.assertIn("src1", new_images_dict)
        self.assertEqual(new_images_dict["src1"], "local/path1")
        self.assertIn("file1", new_files_dict)
        self.assertEqual(new_files_dict["file1"], "local/path2")

        # Verify that assignment_text is a string as expected
        self.assertIsInstance(assignment_text, str)

        # Verify metadata extraction
        self.assertEqual(block_metadata["task_id"], "2")
        self.assertEqual(block_metadata["form_id"], "form2")


if __name__ == '__main__':
    unittest.main()
