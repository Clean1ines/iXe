# processors/json_saver.py
"""
Module for saving parsed data into JSON format.

This module provides the `JSONSaver` class, which handles the serialization
and writing of structured data (typically obtained from a scraper) into
a JSON file. It ensures data is saved in a human-readable format with
proper UTF-8 encoding for international characters.
"""

import json
from pathlib import Path
from typing import Any, Union


class JSONSaver:
    """
    A class responsible for saving data structures to JSON files.

    This class provides a method to serialize a Python object (typically a dictionary
    or list) into a JSON formatted string and write it to a specified file path.
    It uses UTF-8 encoding to support international characters and ensures
    the output is indented for readability.
    """

    def save(self, data: Any, path: Union[str, Path]) -> None:
        """
        Saves the provided data structure to a JSON file.

        This method takes any serializable Python object (e.g., dict, list, str, int)
        and writes its JSON representation to the specified file path. The JSON
        output is formatted with an indentation of 2 spaces and ensures that
        non-ASCII characters (like Cyrillic) are correctly encoded using UTF-8.

        Args:
            data (Any): The Python data structure to be serialized and saved.
                        Must be JSON serializable (e.g., dict, list, tuple, str, int, float, bool, None).
            path (Union[str, Path]): The file path where the JSON data will be saved.
                                     Can be a string or a `pathlib.Path` object.

        Raises:
            TypeError: If the `data` object contains types that are not JSON serializable.
            OSError: If there is an issue writing to the specified file path
                     (e.g., permission denied, invalid path).
        """
        path_obj = Path(path)
        # Ensure the parent directory exists
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(path_obj, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)