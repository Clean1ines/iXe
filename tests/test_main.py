# tests/test_main.py
import unittest
from unittest.mock import patch, MagicMock, ANY
from pathlib import Path
import main
import config # Import config if needed for assertions


class TestMainGetUserSelection(unittest.TestCase):
    """
    Tests for the get_user_selection function in main.py.
    """

    def setUp(self):
        """Set up a test subjects dictionary."""
        self.test_subjects = {
            'ID1': 'Subject A',
            'ID2': 'Subject B',
            'ID3': 'Subject C'
        }

    @patch('builtins.input', side_effect=['1'])
    @patch('builtins.print')  # To suppress print output during test
    def test_valid_input_first(self, mock_print, mock_input):
        """Test selection of the first subject."""
        result = main.get_user_selection(self.test_subjects)
        self.assertEqual(result, ('ID1', 'Subject A'))

    @patch('builtins.input', side_effect=['3'])
    @patch('builtins.print')
    def test_valid_input_last(self, mock_print, mock_input):
        """Test selection of the last subject."""
        result = main.get_user_selection(self.test_subjects)
        self.assertEqual(result, ('ID3', 'Subject C'))

    @patch('builtins.input', side_effect=['abc', '0', '99', '2'])  # Invalid inputs followed by valid
    @patch('builtins.print')
    def test_invalid_inputs_then_valid(self, mock_print, mock_input):
        """Test handling of invalid inputs before a valid one."""
        result = main.get_user_selection(self.test_subjects)
        self.assertEqual(result, ('ID2', 'Subject B'))
        # Assert input was called 4 times (3 invalid, 1 valid)
        self.assertEqual(mock_input.call_count, 4)

    @patch('builtins.input', side_effect=['-1', '4', '1'])  # Out of range inputs, then valid
    @patch('builtins.print')
    def test_out_of_range_input(self, mock_print, mock_input):
        """Test handling of out-of-range numeric inputs."""
        result = main.get_user_selection(self.test_subjects)
        self.assertEqual(result, ('ID1', 'Subject A'))
        self.assertEqual(mock_input.call_count, 3)


class TestMainMainFunction(unittest.TestCase):
    """
    Integration test for the main.main() function, mocking dependencies.
    """

    @patch('builtins.input', side_effect=['1']) # Mock user input to select first subject
    @patch('builtins.print') # Suppress print statements
    @patch('main.fipi_scraper.FIPIScraper')
    @patch('main.html_renderer.HTMLRenderer')
    @patch('main.json_saver.JSONSaver')
    def test_main_flow(self, mock_json_saver_cls, mock_html_renderer_cls, mock_scraper_cls, mock_print, mock_input):
        """
        Test the main flow: get projects -> user selects -> scrape -> process -> save.
        """
        # Mock instances returned by the classes
        mock_scraper_instance = mock_scraper_cls.return_value
        mock_html_renderer_instance = mock_html_renderer_cls.return_value
        mock_json_saver_instance = mock_json_saver_cls.return_value

        # Define test data
        test_subjects = {'TEST_PROJ_ID': 'Test Subject'}
        test_page_data = {'page_name': 'init', 'url': 'http://test.url', 'assignments': ['Q1', 'Q2']}
        test_html_content = '<html><body>Test HTML</body></html>'

        # Configure mock return values
        mock_scraper_instance.get_projects.return_value = test_subjects
        mock_scraper_instance.scrape_page.return_value = test_page_data
        mock_html_renderer_instance.render.return_value = test_html_content

        # Run the main function
        main.main()

        # Assertions to verify the flow
        # 1. Scraper's get_projects was called
        mock_scraper_instance.get_projects.assert_called_once()

        # 2. Scraper's scrape_page was called for each page in the list (init, 1, 2, ..., TOTAL_PAGES)
        # We use TOTAL_PAGES from the config module that the main function uses
        # ИСПРАВЛЕНО: Ожидаем вызовы с тремя аргументами: proj_id, page_name, run_folder (ANY)
        expected_calls = [unittest.mock.call('TEST_PROJ_ID', page_name, ANY) for page_name in ["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)]]
        mock_scraper_instance.scrape_page.assert_has_calls(expected_calls, any_order=False) # Order matters

        # 3. HTML renderer's render and save were called
        # Check render was called for each page's data
        expected_render_calls = [unittest.mock.call(test_page_data)] * len(expected_calls) # Assuming same data returned each time for simplicity in this mock
        # For a more robust test, you'd need to mock scrape_page to return different data or track calls dynamically
        # Here, we check that render was called the correct number of times
        self.assertEqual(mock_html_renderer_instance.render.call_count, len(expected_calls))
        # Check save was called for each page's HTML content
        # The path would be constructed inside main, we can't easily predict the exact Path object without mocking Path calls too deeply
        # We can check the number of calls matches
        self.assertEqual(mock_html_renderer_instance.save.call_count, len(expected_calls))

        # 4. JSON saver's save was called
        self.assertEqual(mock_json_saver_instance.save.call_count, len(expected_calls))


if __name__ == '__main__':
    unittest.main()
