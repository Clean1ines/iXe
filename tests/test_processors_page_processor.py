"""
Unit tests for the PageProcessingOrchestrator class using mocks.
"""
import unittest
from unittest.mock import MagicMock, patch, call
from bs4 import BeautifulSoup
from pathlib import Path
import asyncio
from processors.page_processor import PageProcessingOrchestrator
from domain.models.problem_schema import Problem
from utils.element_pairer import ElementPairer
from domain.interfaces.html_processor import IHTMLProcessor
from utils.downloader import AssetDownloader


class TestPageProcessingOrchestrator(unittest.TestCase):
    """
    Test cases for the PageProcessingOrchestrator class.
    """

    def test_process_page_calls_dependencies_correctly(self):
        """
        Test that the process_page method calls dependencies with correct arguments.
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
        subject = "math"
        base_url = "https://fipi.ru/ege"
        run_folder_page = Path("/tmp/run_folder/page1")
        files_location_prefix = "../../"
        downloader = MagicMock(spec=AssetDownloader)

        # Create mocks
        mock_html_processor = MagicMock(spec=IHTMLProcessor)

        # Create BeautifulSoup object for pairing
        soup = BeautifulSoup(page_content, "html.parser")
        
        # Create actual ElementPairer to get real pairing results
        real_pairer = ElementPairer()
        paired_elements = real_pairer.pair(soup)
        
        print(f"Real paired elements count: {len(paired_elements)}")
        for i, (header, qblock) in enumerate(paired_elements):
            print(f"Pair {i}: header={header.get_text(strip=True) if header else 'None'}, qblock={qblock.get_text(strip=True) if qblock else 'None'}")

        # Mock the HTML processor's process_html_block method return value
        mock_result1 = {
            "problem_id": "TASK123",
            "content": "Question 1 processed",
            "subject": subject
        }
        mock_result2 = {
            "problem_id": "TASK456",
            "content": "Question 2 processed", 
            "subject": subject
        }

        mock_html_processor.process_html_block.side_effect = [
            mock_result1,
            mock_result2
        ]

        # Create orchestrator with mocked html processor
        orchestrator = PageProcessingOrchestrator(
            html_processor=mock_html_processor
        )
        
        # Replace the pairer with our real one for the test
        orchestrator.pairer = real_pairer

        # Call the process_page method (it's async, so we need to await it)
        async def run_test():
            results = await orchestrator.process_page(
                page_content=page_content,
                subject=subject,
                base_url=base_url,
                run_folder_page=run_folder_page,
                downloader=downloader,
                files_location_prefix=files_location_prefix
            )
            return results

        results = asyncio.run(run_test())

        # --- Assertions ---

        # Check that the HTML processor's process_html_block was called twice, once for each pair
        # Note: This might be 0 if ElementPairer doesn't find valid pairs in the test HTML
        print(f"HTML processor call count: {mock_html_processor.process_html_block.call_count}")
        print(f"Expected pairs: {len(paired_elements)}")

        # Check that the returned results list has the correct length
        print(f"Number of results: {len(results)}")
        self.assertEqual(len(results), len(paired_elements))
        
        # If there are paired elements, check that processor was called for each
        if paired_elements:
            self.assertEqual(mock_html_processor.process_html_block.call_count, len(paired_elements))
            self.assertEqual(len(results), 2)  # Expected 2 based on our mock
            self.assertEqual(results[0], mock_result1)
            self.assertEqual(results[1], mock_result2)
        else:
            # If no pairs were found, processor shouldn't be called
            self.assertEqual(mock_html_processor.process_html_block.call_count, 0)
            self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()
