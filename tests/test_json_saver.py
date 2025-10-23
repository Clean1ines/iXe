# tests/test_json_saver.py
import unittest
from pathlib import Path
import tempfile
import json
from processors.json_saver import JSONSaver


class TestJSONSaver(unittest.TestCase):
    """
    Unit tests for the JSONSaver class.
    """

    def setUp(self):
        """
        Set up a temporary directory for test files.
        This directory will be automatically cleaned up after the test.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """
        Clean up the temporary directory after each test.
        """
        self.temp_dir.cleanup()

    def test_save_dict_data(self):
        """
        Test saving a dictionary to a JSON file.
        """
        saver = JSONSaver()
        test_data = {"name": "John", "age": 30, "city": "New York"}
        file_path = self.temp_path / "test_dict.json"

        saver.save(test_data, file_path)

        self.assertTrue(file_path.exists())
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, test_data)

    def test_save_list_data(self):
        """
        Test saving a list to a JSON file.
        """
        saver = JSONSaver()
        test_data = [1, 2, 3, {"key": "value"}]
        file_path = self.temp_path / "test_list.json"

        saver.save(test_data, file_path)

        self.assertTrue(file_path.exists())
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, test_data)

    def test_save_with_cyrillic_characters(self):
        """
        Test saving data containing Cyrillic characters.
        """
        saver = JSONSaver()
        test_data = {"предмет": "Математика", "ответ": "√(x² + y²)"}
        file_path = self.temp_path / "test_cyrillic.json"

        saver.save(test_data, file_path)

        self.assertTrue(file_path.exists())
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, test_data)
        # Ensure the file content itself contains the correct characters when read as text
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("предмет", content)
        self.assertIn("Математика", content)

    def test_save_creates_directories(self):
        """
        Test that save creates parent directories if they don't exist.
        """
        saver = JSONSaver()
        test_data = {"message": "Nested directory test"}
        # Create a path with non-existent subdirectories
        file_path = self.temp_path / "subdir1" / "subdir2" / "nested_file.json"

        saver.save(test_data, file_path)

        self.assertTrue(file_path.exists())
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, test_data)

    def test_save_overwrites_existing_file(self):
        """
        Test that save overwrites an existing file.
        """
        saver = JSONSaver()
        initial_data = {"status": "initial"}
        updated_data = {"status": "updated"}
        file_path = self.temp_path / "overwrite_test.json"

        # Save initial data
        saver.save(initial_data, file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_initial = json.load(f)
        self.assertEqual(loaded_initial, initial_data)

        # Save updated data to the same path
        saver.save(updated_data, file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_updated = json.load(f)
        self.assertEqual(loaded_updated, updated_data)

    def test_save_with_pathlib_path(self):
        """
        Test saving data when the path is provided as a pathlib.Path object.
        """
        saver = JSONSaver()
        test_data = {"path_type": "pathlib.Path"}
        file_path = self.temp_path / "pathlib_test.json"  # This is a Path object

        saver.save(test_data, file_path)

        self.assertTrue(file_path.exists())
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, test_data)

    def test_save_with_string_path(self):
        """
        Test saving data when the path is provided as a string.
        """
        saver = JSONSaver()
        test_data = {"path_type": "string"}
        file_path_str = str(self.temp_path / "string_test.json") # Convert to string

        saver.save(test_data, file_path_str)

        self.assertTrue(Path(file_path_str).exists())
        with open(file_path_str, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, test_data)

    def test_save_invalid_data_type(self):
        """
        Test that saving non-serializable data raises TypeError.
        """
        saver = JSONSaver()
        # A set is not JSON serializable
        invalid_data = {"invalid": set([1, 2, 3])}
        file_path = self.temp_path / "invalid_test.json"

        with self.assertRaises(TypeError):
            saver.save(invalid_data, file_path)

    def test_save_invalid_path(self):
        """
        Test that saving to an invalid path raises OSError (or similar).
        This can happen if the path points to a directory or lacks permissions.
        Testing permissions might require more complex setup, so we test a path pointing to a dir.
        """
        saver = JSONSaver()
        test_data = {"should_fail": True}
        # Use the temporary directory path itself, which should cause an error when trying to write a file to it
        invalid_path = self.temp_path # This is a directory

        with self.assertRaises(OSError): # Can also catch IOError, depending on the system
            saver.save(test_data, invalid_path)


if __name__ == '__main__':
    unittest.main()
    