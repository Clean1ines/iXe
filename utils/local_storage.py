"""Local storage module for managing task answers and statuses."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple


logger = logging.getLogger(__name__)


class LocalStorage:
    """Manages local storage for task answers and their statuses with in-memory caching."""

    def __init__(self, storage_path: Path) -> None:
        """Initializes the LocalStorage with a path to the storage file.

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
            A dictionary containing the stored data. Returns an empty
            dictionary if the file does not exist or is invalid JSON.
        """
        if not self._storage_path.exists():
            return {}
        try:
            with self._storage_path.open('r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    data = json.loads(content)
                    if isinstance(data, dict):
                        return data
                return {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load local storage from %s: %s", self._storage_path, e)
            return {}

    def flush_to_disk(self) -> None:
        """Writes the in-memory data to the storage file."""
        try:
            with self._storage_path.open('w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=4)
        except OSError as e:
            logger.error("Failed to write local storage to %s: %s", self._storage_path, e)
            raise

    def get_answer_and_status(self, task_id: str) -> Tuple[Optional[str], str]:
        """Retrieves the answer and status for a given task ID.

        Args:
            task_id: The unique identifier for the task.

        Returns:
            A tuple containing the answer (or None if not found)
            and the status (defaulting to "not_checked").
        """
        entry = self._data.get(task_id)
        if entry and isinstance(entry, dict):
            answer = entry.get("answer")
            status = entry.get("status", "not_checked")
            return answer, status
        return None, "not_checked"

    def save_answer_and_status(self, task_id: str, answer: str, status: str = "not_checked") -> None:
        """Saves the answer and status for a given task ID.

        Args:
            task_id: The unique identifier for the task.
            answer: The answer string to store.
            status: The status string. Defaults to "not_checked".
        """
        self._data[task_id] = {"answer": answer, "status": status}

    def update_status(self, task_id: str, status: str) -> None:
        """Updates the status for a given task ID.

        Args:
            task_id: The unique identifier for the task.
            status: The new status string.
        """
        entry = self._data.get(task_id)
        if entry and isinstance(entry, dict):
            entry["status"] = status
        else:
            # If the task_id doesn't exist, create a new entry with status only.
            self._data[task_id] = {"status": status}

