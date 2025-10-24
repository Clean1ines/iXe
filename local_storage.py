"""Local storage module for managing task answers and statuses."""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple


class LocalStorage:
    """Manages local storage for task answers and their statuses."""

    def __init__(self, storage_path: Path) -> None:
        """Initializes the LocalStorage with a path to the storage file.

        Args:
            storage_path: Path to the JSON file used for storage.
        """
        self._storage_path = storage_path
        # Ensure the parent directory exists
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> Dict[str, Dict[str, str]]:
        """Loads data from the storage file.

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
        except (json.JSONDecodeError, OSError):
            # In case of an error, return an empty dict
            return {}

    def _save_data(self, data: Dict[str, Dict[str, str]]) -> None:
        """Saves data to the storage file.

        Args:
             The dictionary to save.
        """
        try:
            with self._storage_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError:
            # Consider logging the error
            pass

    def get_answer_and_status(self, task_id: str) -> Tuple[Optional[str], str]:
        """Retrieves the answer and status for a given task ID.

        Args:
            task_id: The unique identifier for the task.

        Returns:
            A tuple containing the answer (or None if not found)
            and the status (defaulting to "not_checked").
        """
        data = self._load_data()
        entry = data.get(task_id)
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
        data = self._load_data()
        data[task_id] = {"answer": answer, "status": status}
        self._save_data(data)

    def update_status(self, task_id: str, status: str) -> None:
        """Updates the status for a given task ID.

        Args:
            task_id: The unique identifier for the task.
            status: The new status string.
        """
        data = self._load_data()
        entry = data.get(task_id)
        if entry and isinstance(entry, dict):
            entry["status"] = status
        else:
            # If the task_id doesn't exist, create a new entry with status only.
            # The answer field might be None or missing.
            data[task_id] = {"status": status}
        self._save_data(data)
