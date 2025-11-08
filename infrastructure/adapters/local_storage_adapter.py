"""Local storage adapter module for managing task answers and statuses."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from domain.interfaces.infrastructure_adapters import IStorageProvider


logger = logging.getLogger(__name__)


class LocalStorageAdapterAdapter(IStorageProvider):
    """Manages local storage for task answers and their statuses with in-memory caching."""

    def __init__(self, storage_path: Path) -> None:
        """Initializes the LocalStorageAdapter with a path to the storage file.

        Args:
            storage_path: Path to the JSON file used for storage.
        """
        self._storage_path = storage_path
        # Ensure the parent directory exists
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        # Load data into memory once at initialization
        self._data: Dict[str, Dict[str, str]] = self._load_data_from_disk()

    def _load_data_from_disk(self) -> Dict[str, Dict[str, str]]:
        """Loads data from the storage file on disk.

        Returns:
            A dictionary with the loaded data.
        """
        if self._storage_path.exists():
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from {self._storage_path}, using empty dict")
                    return {}
        else:
            # Create file with empty dict if it doesn't exist
            self._save_data_to_disk({})
            return {}

    def _save_data_to_disk(self) -> None:
        """Saves the in-memory data to the storage file on disk."""
        with open(self._storage_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_answer_and_status(self, problem_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Gets the stored answer and status for a problem.

        Args:
            problem_id: The ID of the problem.

        Returns:
            A tuple of (answer, status), or (None, None) if not found.
        """
        entry = self._data.get(problem_id)
        if entry:
            return entry.get('answer'), entry.get('status')
        return None, None

    def save_answer_and_status(self, problem_id: str, answer: str, status: str) -> None:
        """Saves an answer and its status for a problem.

        Args:
            problem_id: The ID of the problem.
            answer: The answer to save.
            status: The status of the answer (e.g., 'correct', 'incorrect').
        """
        if problem_id not in self._data:
            self._data[problem_id] = {}
        self._data[problem_id]['answer'] = answer
        self._data[problem_id]['status'] = status
        # Persist changes to disk
        self._save_data_to_disk()
