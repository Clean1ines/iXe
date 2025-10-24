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
        # Исправлено: после ввода -1 и 4 (оба неверные), третий ввод - '1', что соответствует ID1
        self.assertEqual(result, ('ID1', 'Subject A'))
        self.assertEqual(mock_input.call_count, 3)


class TestMainMainFunction(unittest.TestCase):
    """
    Integration test for the main.main() function, mocking dependencies.
    """

    @patch('builtins.input', side_effect=['1', '']) # Mock user input to select first subject, then Enter to exit
    @patch('builtins.print') # Suppress print statements
    @patch('main.fipi_scraper.FIPIScraper')
    @patch('main.html_renderer.HTMLRenderer')
    @patch('main.json_saver.JSONSaver')
    # NEW: Mock API-related components to prevent real server startup
    @patch('main.LocalStorage')
    @patch('main.FIPIAnswerChecker')
    @patch('main.create_app')
    @patch('main.start_api_server')
    @patch('threading.Thread')
    @patch('main.ProblemStorage') # NEW: Mock ProblemStorage
    def test_main_flow(self, mock_problem_storage_cls, mock_thread, mock_start_api_server, mock_create_app, mock_checker_cls, mock_storage_cls, mock_json_saver_cls, mock_html_renderer_cls, mock_scraper_cls, mock_print, mock_input):
        """
        Test the main flow: get projects -> user selects -> scrape -> process -> save.
        API components are mocked to prevent actual server startup.
        NEW: Also mocks ProblemStorage.
        """
        # Mock instances returned by the classes
        mock_scraper_instance = mock_scraper_cls.return_value
        mock_html_renderer_instance = mock_html_renderer_cls.return_value
        mock_json_saver_instance = mock_json_saver_cls.return_value
        # NEW: Mock API components
        mock_storage_instance = mock_storage_cls.return_value
        mock_checker_instance = mock_checker_cls.return_value
        mock_app_instance = mock_create_app.return_value
        # NEW: Mock ProblemStorage
        mock_problem_storage_instance = mock_problem_storage_cls.return_value

        # Define test data
        test_subjects = {'TEST_PROJ_ID': 'Test Subject'}
        # NEW: Добавим blocks_html и task_metadata в test_page_data
        test_page_data = {
            'page_name': 'init',
            'url': 'http://test.url',
            'assignments': ['Q1', 'Q2'],
            'blocks_html': ['<p>Block1</p>', '<p>Block2</p>'], # 2 блока для теста render_block
            'task_metadata': [{'task_id': 'task1', 'form_id': 'form1'}, {'task_id': 'task2', 'form_id': 'form2'}]
        }
        test_problems = [MagicMock(), MagicMock()] # Example Problem objects
        test_html_content = '<html><body>Test HTML</body></html>'

        # Configure mock return values
        mock_scraper_instance.get_projects.return_value = test_subjects
        # NEW: scrape_page теперь возвращает кортеж (problems, scraped_data)
        mock_scraper_instance.scrape_page.return_value = (test_problems, test_page_data)
        mock_html_renderer_instance.render.return_value = test_html_content
        # NEW: Мокаем render_block, чтобы он возвращал фиктивный HTML
        mock_html_renderer_instance.render_block.return_value = '<html>Block HTML</html>'

        # NEW: Configure mocked API components to return sensible mocks
        mock_storage_cls.return_value = mock_storage_instance
        mock_checker_cls.return_value = mock_checker_instance
        mock_create_app.return_value = mock_app_instance
        # NEW: Configure mocked ProblemStorage
        mock_problem_storage_cls.return_value = mock_problem_storage_instance

        # Run the main function
        main.main()

        # Assertions to verify the flow
        # 1. Scraper's get_projects was called
        mock_scraper_instance.get_projects.assert_called_once()

        # 2. Scraper's scrape_page was called for each page in the list (init, 1, 2, ..., TOTAL_PAGES)
        # We use TOTAL_PAGES from the config module that the main function uses
        # ИСПРАВЛЕНО: Ожидаем вызовы с тремя аргументами: proj_id, page_name, run_folder (ANY)
        expected_scrape_calls = [unittest.mock.call('TEST_PROJ_ID', page_name, ANY) for page_name in ["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)]]
        mock_scraper_instance.scrape_page.assert_has_calls(expected_scrape_calls, any_order=False) # Order matters

        # 3. NEW: Verify API components were initialized and server started in thread
        mock_storage_cls.assert_called_once()
        mock_checker_cls.assert_called_once()
        mock_create_app.assert_called_once()
        mock_thread.assert_called_once()
        mock_start_api_server.assert_not_called() # Should not be called directly, only via thread target

        # 4. NEW: Verify ProblemStorage was initialized and save_problems was called for each page
        mock_problem_storage_cls.assert_called_once() # Called once in main() with the path
        # save_problems should be called once per page
        self.assertEqual(mock_problem_storage_instance.save_problems.call_count, len(expected_scrape_calls))
        # Assert it was called with the list of problems each time
        expected_save_problem_calls = [unittest.mock.call(test_problems) for _ in range(len(expected_scrape_calls))]
        mock_problem_storage_instance.save_problems.assert_has_calls(expected_save_problem_calls, any_order=False)

        # 5. HTML renderer's render and render_block and save were called
        # Check render was called for each page's data (with page_name)
        expected_render_calls = [unittest.mock.call(test_page_data, page_name=page_name) for page_name in ["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)]]
        mock_html_renderer_instance.render.assert_has_calls(expected_render_calls, any_order=False)

        # Check render_block was called for each block in each page's data
        num_blocks_per_page = len(test_page_data.get('blocks_html', []))
        expected_render_block_calls = []
        for page_name in ["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)]:
            for block_idx, block_content in enumerate(test_page_data.get('blocks_html', [])):
                # ИСПРАВЛЕНО: добавлены task_id и form_id из task_metadata
                metadata = test_page_data.get('task_metadata', [])[block_idx]
                task_id = metadata.get('task_id', '')
                form_id = metadata.get('form_id', '')
                # render_block вызывается с позиционными аргументами block_content, block_idx
                # и именованными asset_path_prefix, page_name, task_id, form_id
                expected_render_block_calls.append(
                    unittest.mock.call(
                        block_content,
                        block_idx,
                        asset_path_prefix="../assets",
                        page_name=page_name,
                        task_id=task_id,
                        form_id=form_id
                    )
                )
        mock_html_renderer_instance.render_block.assert_has_calls(expected_render_block_calls, any_order=False)

        # Check save was called:
        # - once for the main HTML page per scraped page
        # - once for each block's HTML per scraped page
        expected_save_calls_for_pages = len(expected_scrape_calls)
        expected_save_calls_for_blocks = len(expected_scrape_calls) * num_blocks_per_page
        expected_total_save_calls = expected_save_calls_for_pages + expected_save_calls_for_blocks

        self.assertEqual(mock_html_renderer_instance.save.call_count, expected_total_save_calls)
        # Example: 51 pages * (1 main HTML + 2 blocks HTML) = 51 * 3 = 153 calls
        # If TOTAL_PAGES = 50, then pages are ["init"] + ["1", ..., "50"] = 51 page name -> 51 scrape calls
        # 51 main HTML saves + 51 * 2 block saves = 51 + 102 = 153 total saves
        # self.assertEqual(mock_html_renderer_instance.save.call_count, 153) # This would be specific check for TOTAL_PAGES=50 and 2 blocks


        # 6. JSON saver's save was called for each page's data
        self.assertEqual(mock_json_saver_instance.save.call_count, len(expected_scrape_calls))


if __name__ == '__main__':
    unittest.main()
