"""
Unit tests for the PageProcessingOrchestrator class using mocks.
"""
import unittest
from unittest.mock import MagicMock, patch, call
from bs4 import BeautifulSoup
from pathlib import Path
from processors.page_processor import PageProcessingOrchestrator
from models.problem_schema import Problem
from utils.element_pairer import ElementPairer
from utils.metadata_extractor import MetadataExtractor
from models.problem_builder import ProblemBuilder
from utils.downloader import AssetDownloader


class TestPageProcessingOrchestrator(unittest.TestCase):
    """
    Test cases for the PageProcessingOrchestrator class.
    """

    def setUp(self):
        """
        Set up mocks and orchestrator instance for tests.
        """
        # Create mocks for dependencies
        self.mock_asset_downloader = MagicMock(spec=AssetDownloader)
        self.mock_asset_downloader_factory = MagicMock(return_value=self.mock_asset_downloader)

        self.mock_processor1 = MagicMock()
        self.mock_processor2 = MagicMock()
        self.mock_processors = [self.mock_processor1, self.mock_processor2]

        self.mock_pairer = MagicMock(spec=ElementPairer)
        self.mock_metadata_extractor = MagicMock(spec=MetadataExtractor)
        self.mock_problem_builder = MagicMock(spec=ProblemBuilder)

        # Patch the internal classes used by the orchestrator during instantiation
        # We patch them to return our specific mock instances
        with patch('processors.page_processor.ElementPairer', return_value=self.mock_pairer), \
             patch('processors.page_processor.MetadataExtractor', return_value=self.mock_metadata_extractor), \
             patch('processors.page_processor.ProblemBuilder', return_value=self.mock_problem_builder):
            self.orchestrator = PageProcessingOrchestrator(
                asset_downloader_factory=self.mock_asset_downloader_factory,
                processors=self.mock_processors
            )

    def test_process_calls_dependencies_correctly(self):
        """
        Test that the process method calls dependencies with correct arguments.
        """
        # Prepare test data
        page_content = """
        <html>
            <body>
                <div class="header-container">
                    <span class="canselect">TASK123</span>
                    <span class="answer-button" onclick="checkButtonClick('form123')"></span>
                </div>
                <div class="qblock">Question 1 content</div>
                <div class="header-container">
                    <span class="canselect">TASK456</span>
                </div>
                <div class="qblock">Question 2 content</div>
            </body>
        </html>
        """
        proj_id = "math"
        page_num = "01"
        run_folder = Path("/tmp/run_folder")
        base_url = "https://fipi.ru/ege  "
        files_location_prefix = "../../"
        page_obj = MagicMock() # Mock Playwright page object

        # Mock the return value of ElementPairer.pair
        # It should return a list of tuples (header_container, qblock)
        soup = BeautifulSoup(page_content, "html.parser")
        header1 = soup.find_all("div", class_="header-container")[0]
        qblock1 = soup.find_all("div", class_="qblock")[0]
        header2 = soup.find_all("div", class_="header-container")[1]
        qblock2 = soup.find_all("div", class_="qblock")[1]
        paired_elements = [(header1, qblock1), (header2, qblock2)]

        self.mock_pairer.pair.return_value = paired_elements

        # Mock the *already existing* BlockProcessor instance inside the orchestrator
        # This is the BlockProcessor that was created during setUp
        mock_internal_block_processor = MagicMock()
        # We need to access the actual BlockProcessor instance created during setUp
        # It was created with the patched dependencies
        # Let's patch the BlockProcessor.process method where it's called from page_processor
        # But since the orchestrator already has an instance, we patch its method directly
        # First, get the instance
        # The orchestrator creates a BlockProcessor instance in its __init__ if block_processor is None
        # The instance is stored in self.block_processor
        # We need to mock the process method of that specific instance
        # We can do this by replacing the instance with our mock
        original_block_processor = self.orchestrator.block_processor

        # Mock the process method of the internal BlockProcessor instance
        mock_internal_block_processor_process = MagicMock()
        original_block_processor.process = mock_internal_block_processor_process

        # Mock the BlockProcessor's process method return value
        # Assuming BlockProcessor returns: processed_html, assignment_text, new_images, new_files, problem, metadata
        mock_problem1 = MagicMock(spec=Problem)
        mock_problem1.problem_id = "TASK123"
        mock_problem2 = MagicMock(spec=Problem)
        mock_problem2.problem_id = "TASK456"

        original_block_processor.process.side_effect = [
            ("Processed HTML 1", "Assignment 1", {"img1": "path1"}, {"file1": "path1"}, mock_problem1, {"meta1": "data1"}),
            ("Processed HTML 2", "Assignment 2", {"img2": "path2"}, {"file2": "path2"}, mock_problem2, {"meta2": "data2"})
        ]

        # Call the process method
        problems, scraped_data = self.orchestrator.process(
            page_content=page_content,
            proj_id=proj_id,
            page_num=page_num,
            run_folder=run_folder,
            base_url=base_url,
            files_location_prefix=files_location_prefix,
            page=page_obj
        )

        # --- Assertions ---

        # 1. Check that ElementPairer.pair was called once with the correct soup object
        self.mock_pairer.pair.assert_called_once()
        # Get the argument passed to pair and check its type and content
        args, kwargs = self.mock_pairer.pair.call_args
        self.assertIsInstance(args[0], BeautifulSoup)
        self.assertEqual(args[0].find("body").find("div", class_="header-container").get_text(strip=True), "TASK123")

        # 2. Check that the internal BlockProcessor.process was called twice, once for each pair
        self.assertEqual(original_block_processor.process.call_count, 2)

        # 3. Check the calls to BlockProcessor.process
        expected_calls = [
            call(
                header_container=header1,
                qblock=qblock1,
                block_index=0,
                page_num=page_num,
                page_assets_dir=run_folder / page_num / "assets",
                proj_id=proj_id,
                base_url=base_url,
                page=page_obj,
                files_location_prefix=files_location_prefix
            ),
            call(
                header_container=header2,
                qblock=qblock2,
                block_index=1,
                page_num=page_num,
                page_assets_dir=run_folder / page_num / "assets",
                proj_id=proj_id,
                base_url=base_url,
                page=page_obj,
                files_location_prefix=files_location_prefix
            )
        ]
        original_block_processor.process.assert_has_calls(expected_calls)

        # 4. Check that the returned problems list has the correct length and content
        self.assertEqual(len(problems), 2)
        self.assertEqual(problems[0], mock_problem1)
        self.assertEqual(problems[1], mock_problem2)

        # 5. Check that the returned scraped_data has the correct structure and content
        self.assertEqual(scraped_data["page_name"], page_num)
        self.assertEqual(scraped_data["url"], f"{base_url}?proj={proj_id}&page={page_num}")
        self.assertEqual(scraped_data["assignments"], ["Assignment 1", "Assignment 2"])
        self.assertEqual(scraped_data["blocks_html"], ["Processed HTML 1", "Processed HTML 2"])
        expected_images = {"img1": "path1", "img2": "path2"}
        expected_files = {"file1": "path1", "file2": "path2"}
        self.assertEqual(scraped_data["images"], expected_images)
        self.assertEqual(scraped_data["files"], expected_files)
        expected_metadata = [{"meta1": "data1"}, {"meta2": "data2"}]
        self.assertEqual(scraped_data["task_metadata"], expected_metadata)


if __name__ == '__main__':
    unittest.main()
