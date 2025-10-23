# tests/test_config.py
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

# Импортируем модуль config. Так как config.py находится в корне проекта (предположительно),
# относительно этого теста, мы можем импортировать его напрямую, если тест запускается из корня.
# Альтернативно, можно добавить путь к sys.path.
# import sys
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class TestConfigDefaults(unittest.TestCase):
    """
    Tests that configuration variables load default values when environment variables are not set.
    """

    def test_default_values(self):
        """Test default values for all config variables."""
        # Ensure environment variables that could override defaults are not set for this test
        # This can be done by temporarily clearing them in the environment mock
        with patch.dict(os.environ, {}, clear=True):
            # Reload the config module to pick up the patched environment
            import importlib
            importlib.reload(config)

            # Test string defaults
            # ИСПРАВЛЕНО: Проверяем новые переменные
            self.assertEqual(config.FIPI_QUESTIONS_URL, "https://ege.fipi.ru/bank/questions.php")
            self.assertEqual(config.FIPI_SUBJECTS_URL, "https://ege.fipi.ru/bank/")
            self.assertEqual(config.FIPI_DEFAULT_PROJ_ID, "AC437B34557F88EA4115D2F374B0A07B")
            self.assertEqual(config.BROWSER_USER_AGENT, "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36")

            # Test int default
            self.assertEqual(config.TOTAL_PAGES, 98)

            # Test bool default (True if 'True', case insensitive, False otherwise)
            self.assertTrue(config.BROWSER_HEADLESS)

            # Test Path defaults
            expected_data_root = Path.home() / "iXe" / "data"
            expected_output_dir = Path("problems")
            self.assertEqual(config.DATA_ROOT, expected_data_root.resolve())
            self.assertEqual(config.OUTPUT_DIR, expected_output_dir.resolve())
            self.assertTrue(config.DATA_ROOT.is_absolute())
            self.assertTrue(config.OUTPUT_DIR.is_absolute())


class TestConfigFromEnv(unittest.TestCase):
    """
    Tests that configuration variables correctly load from environment variables.
    """

    def test_values_from_env(self):
        """Test loading values from environment variables."""
        env_vars = {
            # ИСПРАВЛЕНО: Используем новые переменные окружения
            'FIPI_SUBJECTS_URL': 'https://test.fipi.ru/', # URL для списка предметов
            'FIPI_QUESTIONS_URL': 'https://test.fipi.ru/questions.php', # URL для вопросов
            'FIPI_DEFAULT_PROJ_ID': 'TEST_PROJ_ID',
            'TELEGRAM_BOT_TOKEN': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            'TELEGRAM_USER_ID': '987654321',
            'FIPI_DATA_ROOT': '/tmp/test_data',
            'OUTPUT_DIR': 'custom_output',
            'TOTAL_PAGES': '50',
            'BROWSER_USER_AGENT': 'Test User Agent',
            'BROWSER_HEADLESS': 'False'
        }
        with patch.dict(os.environ, env_vars):
            import importlib
            importlib.reload(config)

            # ИСПРАВЛЕНО: Проверяем новые переменные
            self.assertEqual(config.FIPI_SUBJECTS_URL, 'https://test.fipi.ru/')
            self.assertEqual(config.FIPI_QUESTIONS_URL, 'https://test.fipi.ru/questions.php')
            self.assertEqual(config.FIPI_DEFAULT_PROJ_ID, 'TEST_PROJ_ID')
            self.assertEqual(config.TELEGRAM_BOT_TOKEN, '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11')
            self.assertEqual(config.TELEGRAM_USER_ID, '987654321')
            self.assertEqual(config.DATA_ROOT, Path('/tmp/test_data').resolve())
            self.assertEqual(config.OUTPUT_DIR, Path('custom_output').resolve())
            self.assertEqual(config.TOTAL_PAGES, 50)
            self.assertEqual(config.BROWSER_USER_AGENT, 'Test User Agent')
            self.assertFalse(config.BROWSER_HEADLESS) # Should be False if 'False' is set

    def test_total_pages_type_conversion(self):
        """Test that TOTAL_PAGES is correctly converted from string to int."""
        with patch.dict(os.environ, {'TOTAL_PAGES': '100'}):
            import importlib
            importlib.reload(config)
            self.assertIsInstance(config.TOTAL_PAGES, int)
            self.assertEqual(config.TOTAL_PAGES, 100)

    def test_browser_headless_boolean_conversion(self):
        """Test that BROWSER_HEADLESS correctly converts string to boolean."""
        # Test True cases (any value except 'false', 'False', 'FALSE')
        true_values = ['True', 'true', 'TRUE', 'other', '1', 'yes', 'anything_else']
        for true_val in true_values:
            with self.subTest(env_val=true_val):
                with patch.dict(os.environ, {'BROWSER_HEADLESS': true_val}):
                    import importlib
                    importlib.reload(config)
                    self.assertTrue(config.BROWSER_HEADLESS)

        # Test False cases
        false_values = ['False', 'false', 'FALSE']
        for false_val in false_values:
            with self.subTest(env_val=false_val):
                with patch.dict(os.environ, {'BROWSER_HEADLESS': false_val}):
                    import importlib
                    importlib.reload(config)
                    self.assertFalse(config.BROWSER_HEADLESS)


if __name__ == '__main__':
    unittest.main()
