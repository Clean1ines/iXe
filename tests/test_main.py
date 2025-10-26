"""
Unit tests for the main.py script.
This module uses mocking to test the control flow of the main function
without performing actual network requests, file I/O, or database operations.
NEW: Updated to reflect the new internal run_server function used as target for threading.
NEW: Updated to reflect the new signature of HTMLRenderer.render_block which includes task_id, form_id, page_name.
NEW: Updated to reflect the new signature of HTMLRenderer.__init__ which accepts a DatabaseManager instance.
NEW: Updated to reflect the new signature of HTMLRenderer.render which accepts a page_name.
NEW: Updated to reflect the new asset_path_prefix used in render_block call.
"""
import unittest
from unittest.mock import patch, MagicMock, ANY
import config # Import config to access TOTAL_PAGES
import main # Import the main module itself to call main.main()

class TestMainMainFunction(unittest.TestCase):
    """
    Test suite for the main.main() function.
    """

    @patch('builtins.input', side_effect=['1', '']) # Mock user input to select first subject, then Enter to exit
    @patch('builtins.print') # Suppress print statements
    @patch('main.fipi_scraper.FIPIScraper')
    @patch('main.html_renderer.HTMLRenderer')
    @patch('main.json_saver.JSONSaver')
    # NEW: Mock API-related components to prevent real server startup
    # REMOVED: @patch('main.LocalStorage') # OLD: No longer used
    @patch('main.FIPIAnswerChecker')
    @patch('main.create_app')
    @patch('threading.Thread') # NEW: Mock threading.Thread to prevent actual thread creation
    @patch('main.DatabaseManager') # NEW: Mock DatabaseManager
    def test_main_flow(self, mock_db_manager_cls, mock_thread_cls, mock_create_app, mock_checker_cls, mock_json_saver_cls, mock_html_renderer_cls, mock_scraper_cls, mock_print, mock_input):
        """
        Test the main flow: get projects -> user selects -> scrape -> process -> save.
        API components are mocked to prevent actual server startup.
        NEW: Also mocks DatabaseManager.
        NEW: Mock threading.Thread to prevent actual thread creation and uvicorn.run call.
        NEW: Updated to reflect the new internal run_server function used as target.
        """
        # Mock instances returned by the classes
        mock_scraper_instance = mock_scraper_cls.return_value
        mock_html_renderer_instance = mock_html_renderer_cls.return_value
        mock_json_saver_instance = mock_json_saver_cls.return_value
        # NEW: Mock API components
        # OLD: mock_storage_instance = mock_storage_cls.return_value # No longer used
        mock_checker_instance = mock_checker_cls.return_value
        mock_app_instance = mock_create_app.return_value
        mock_thread_instance = mock_thread_cls.return_value # NEW: Mock thread instance
        # NEW: Mock DatabaseManager
        mock_db_manager_instance = mock_db_manager_cls.return_value

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
        # NEW: Для теста scrape_page возвращает одни и те же данные для всех страниц, но этого достаточно для проверки логики вызовов
        mock_scraper_instance.scrape_page.return_value = (test_problems, test_page_data)
        mock_html_renderer_instance.render.return_value = test_html_content
        # NEW: Мокаем render_block, чтобы он возвращал фиктивный HTML
        mock_html_renderer_instance.render_block.return_value = '<html>Block HTML</html>'

        # NEW: Configure mocked API components to return sensible mocks
        # OLD: mock_storage_cls.return_value = mock_storage_instance # No longer used
        mock_checker_cls.return_value = mock_checker_instance
        mock_create_app.return_value = mock_app_instance
        # NEW: Configure mocked thread to return a mock instance
        mock_thread_cls.return_value = mock_thread_instance
        # NEW: Configure mocked DatabaseManager
        mock_db_manager_cls.return_value = mock_db_manager_instance

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

        # 3. NEW: Verify API components were initialized and thread was created with correct arguments
        # OLD: mock_storage_cls.assert_called_once() # No longer used
        mock_checker_cls.assert_called_once()
        mock_create_app.assert_called_once_with(mock_db_manager_instance, mock_checker_instance) # Passes db_manager and checker
        # NEW: Verify threading.Thread was called once with the correct target (the internal run_server function) and kwargs
        # The target should now be the internal function defined in main.py, not uvicorn.run directly
        mock_thread_cls.assert_called_once()
        # Get the call arguments
        call_args = mock_thread_cls.call_args
        kwargs_passed_to_thread = call_args[1] # Keyword arguments passed to Thread constructor
        # Assert 'target' is the internal run_server function (we cannot easily assert its identity without importing it)
        # Instead, we can assert it's a function (callable)
        self.assertTrue(callable(kwargs_passed_to_thread['target']), "Thread target should be callable")
        # Assert 'args' contains the expected arguments for the run_server function (app, host, port)
        expected_run_server_args = (mock_app_instance, "127.0.0.1", 8000)
        actual_run_server_args = kwargs_passed_to_thread['args']
        self.assertEqual(actual_run_server_args, expected_run_server_args)
        # Assert daemon was set
        self.assertTrue(mock_thread_instance.daemon)

        # 4. NEW: Verify DatabaseManager was initialized, initialize_db was called, and save_problems was called for each page
        mock_db_manager_cls.assert_called_once() # Called once in main() with the path
        # Get the arguments used to call DatabaseManager constructor
        db_manager_call_args = mock_db_manager_cls.call_args
        # The path should be relative to run_folder
        # We can't easily assert the exact path without knowing the timestamp, but we know it happens
        mock_db_manager_instance.initialize_db.assert_called_once() # initialize_db called once
        # save_problems should be called once per page
        self.assertEqual(mock_db_manager_instance.save_problems.call_count, len(expected_scrape_calls))
        # Assert it was called with the list of problems each time
        expected_save_problem_calls = [unittest.mock.call(test_problems) for _ in range(len(expected_scrape_calls))]
        mock_db_manager_instance.save_problems.assert_has_calls(expected_save_problem_calls, any_order=False)

        # 5. HTML renderer's render and render_block and save were called
        # Check render was called the correct number of times
        expected_render_call_count = len(expected_scrape_calls)
        self.assertEqual(mock_html_renderer_instance.render.call_count, expected_render_call_count)
        # Check render was called with correct arguments (scraped_data, page_name=page_name)
        # We check the page_name argument specifically
        # ИСПРАВЛЕНО: Проверяем позиционный аргумент args[1] вместо именованного kwargs['page_name']
        actual_render_calls = mock_html_renderer_instance.render.call_args_list
        page_names_for_scraped_pages = ["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)]
        for i, call in enumerate(actual_render_calls):
            args, kwargs = call
            # args[0] is scraped_data
            # args[1] is page_name
            # kwargs should be empty for this call in main.py
            expected_page_name = page_names_for_scraped_pages[i]
            self.assertEqual(args[1], expected_page_name) # Check the second positional argument


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
                # ИСПРАВЛЕНО: asset_path_prefix изменён на '../../assets' для соответствия реальному коду
                expected_render_block_calls.append(
                    unittest.mock.call(
                        block_content,
                        block_idx,
                        asset_path_prefix="../../assets", # ИСПРАВЛЕНО: Соответствует main.py
                        page_name=page_name,
                        task_id=task_id,
                        form_id=form_id
                    )
                )
        mock_html_renderer_instance.render_block.assert_has_calls(expected_render_block_calls, any_order=False)

        # 6. JSON saver's save was called
        expected_json_save_call_count = len(expected_scrape_calls)
        self.assertEqual(mock_json_saver_instance.save.call_count, expected_json_save_call_count)

        # 7. NEW: Verify HTML renderer's save was called for page HTML and block HTML
        # Calculate expected save calls: 1 page HTML + N blocks HTML per page
        num_pages = len(["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)])
        expected_save_call_count = num_pages + (num_pages * num_blocks_per_page) # e.g., 51 + (51 * 2) = 153 for default config
        self.assertEqual(mock_html_renderer_instance.save.call_count, expected_save_call_count)
        # Optionally, check if save was called with a path containing '.html'
        for call in mock_html_renderer_instance.save.call_args_list:
            args, kwargs = call
            path_str = str(args[1]) # Second argument is the path
            self.assertTrue(path_str.endswith('.html'), f"Save called with non-HTML path: {path_str}")

if __name__ == '__main__':
    unittest.main()
