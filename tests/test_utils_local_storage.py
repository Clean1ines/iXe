"""Tests for the LocalStorageAdapter class."""

import json
import os
import tempfile
import unittest
from pathlib import Path

# Импортируем класс, используя относительный путь или прямое выполнение
# В данном случае, предполагается, что структура проекта такова, что
# utils/ находится в корне проекта, рядом с tests/
# Для pytest, запускаемого из корня, sys.path может не включать '.' по умолчанию.
# Альтернатива - сделать utils пакетом (__init__.py) и использовать относительные импорты,
# но в данном случае, чтобы избежать создания лишних файлов, можно модифицировать путь.
# Однако, самый простой способ - это убедиться, что pytest запускается из корня,
# и файл находится в utils.local_storage. Если структура не такова, нужно явно указать путь.
# Предполагаем, что файл utils/local_storage.py находится в корне проекта относительно tests/
# и что Python может его импортировать, если он находится в той же директории или sys.path.

# Для этого примера, мы будем импортировать напрямую, как если бы файл был в той же директории или в PYTHONPATH.
# Если структура другая, нужно будет создать __init__.py и использовать относительные пути.
# Пока что, если файл utils/local_storage.py находится в корне, относительно которого запускается pytest,
# и рядом с ним лежит папка tests/, то нужно указать путь к utils в PYTHONPATH или
# положить файл локально в tests/ для теста. Но это не рекомендуется.
# Правильный путь - убедиться, что utils - это пакет.

# Однако, чтобы не усложнять, и если структура такова, что pytest запускается из корня проекта
# и utils/ находится в корне, то можно использовать:
# PYTHONPATH=. pytest tests/
# Или убедиться, что структура позволяет импорт.
# В текущем случае, если utils/local_storage.py находится в корне, относительно которого запускается команда,
# и рядом лежит tests/, то для импорта внутри папки tests/ нужно, чтобы Python нашел модуль utils.
# Это достигается либо установкой пакета (pip install -e .), либо добавлением корня в sys.path в тесте.
# Пока что, предположим, что структура позволяет импорт, иначе нужно создать пакет.

# ВАЖНО: Если utils не является пакетом (нет __init__.py) и файлы находятся так:
# project_root/
#   utils/
#     local_storage.py
#   tests/
#     test_utils_local_storage.py
# То стандартный импорт не сработает из-за особенностей Python и pytest.
# Нужно либо сделать utils пакетом, либо запускать pytest с корректным PYTHONPATH.

# В целях соответствия запросу, я оставлю импорт как есть, предполагая, что структура или запуск позволяют его.
# Если возникает ошибка, как в вашем случае, то нужно:
# 1. Создать файл utils/__init__.py (даже пустой)
# 2. Запускать pytest из корня проекта (где лежит utils/ и tests/)

# В этом файле (tests/test_utils_local_storage.py) делаем импорт:
# --- НАЧАЛО КОММЕНТАРИЯ ОБ ИМПОРТЕ ---
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent)) # Добавить корень проекта в путь
# from infrastructure.adapters.local_storage_adapter import LocalStorageAdapterAdapter
# --- КОНЕЦ КОММЕНТАРИЯ ---

# Ниже приведен вариант с добавлением пути, чтобы тест работал из корня проекта,
# даже если utils не является пакетом или pytest запускается из неправильной директории.
# Это менее предпочтительно, чем правильная настройка пакета, но решает проблему импорта.

import sys
from pathlib import Path

# Добавляем родительскую директорию (корень проекта) в sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.adapters.local_storage_adapter import LocalStorageAdapterAdapter


class TestLocalStorageAdapterAdapter(unittest.TestCase):
    """Test case for LocalStorageAdapter class."""

    def test_save_and_get(self) -> None:
        """Test saving and retrieving an answer and status."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        storage = LocalStorageAdapterAdapter(tmp_path)
        storage.save_answer_and_status("task1", "ans1", "correct")

        answer, status = storage.get_answer_and_status("task1")
        self.assertEqual(answer, "ans1")
        self.assertEqual(status, "correct")

        # Cleanup
        os.unlink(tmp_path)

    def test_get_nonexistent(self) -> None:
        """Test retrieving a non-existent task ID."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        storage = LocalStorageAdapterAdapter(tmp_path)
        answer, status = storage.get_answer_and_status("task999")

        self.assertIsNone(answer)
        self.assertEqual(status, "not_checked")

        # Cleanup
        os.unlink(tmp_path)

    def test_update_status(self) -> None:
        """Test updating the status of an existing task."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        storage = LocalStorageAdapterAdapter(tmp_path)
        storage.save_answer_and_status("task1", "ans1", "not_checked")

        # Verify initial state
        answer, status = storage.get_answer_and_status("task1")
        self.assertEqual(answer, "ans1")
        self.assertEqual(status, "not_checked")

        # Update status
        storage.update_status("task1", "incorrect")

        # Verify updated state
        answer, status = storage.get_answer_and_status("task1")
        self.assertEqual(answer, "ans1")  # Answer should remain
        self.assertEqual(status, "incorrect")  # Status should update

        # Cleanup
        os.unlink(tmp_path)

    def test_persistence(self) -> None:
        """Test that data persists between different instances of LocalStorageAdapter."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        # Create first instance, save data
        storage1 = LocalStorageAdapterAdapter(tmp_path)
        storage1.save_answer_and_status("task_persist", "persisted_answer", "correct")

        # Create a second instance with the same file path
        storage2 = LocalStorageAdapterAdapter(tmp_path)

        # Retrieve data using the second instance
        answer, status = storage2.get_answer_and_status("task_persist")

        self.assertEqual(answer, "persisted_answer")
        self.assertEqual(status, "correct")

        # Cleanup
        os.unlink(tmp_path)
