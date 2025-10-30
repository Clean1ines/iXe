#!/usr/bin/env python3
"""
Скрипт для миграции offline_html в базу данных fipi_data.db.

Извлекает содержимое задачи из файлов /frontend/public/blocks/math,
удаляет обёртку .processed_qblock, формы и статусы,
и сохраняет очищенное содержимое в поле offline_html в таблице problems.

Предполагает, что:
1. В моделях и БД уже добавлено поле offline_html.
2. Файлы в blocks/math имеют структуру .processed_qblock -> .qblock.
3. Атрибут data-task-id в .processed_qblock содержит суффикс идентификатора задачи, соответствующий суффиксу problem_id в БД.
   Например, data-task-id="4CBD4E" соответствует problem_id="init_4CBD4E".
"""

import os
import re
import sqlite3
from pathlib import Path

# --- Конфигурация ---
# Путь к базе данных
DB_PATH = Path("data/math/fipi_data.db")
# Путь к директории с HTML-файлами блоков
BLOCKS_DIR = Path("frontend/public/blocks/math")
# --- /Конфигурация ---

def add_offline_html_column(db_path: Path):
    """Добавляет столбец offline_html в таблицу problems, если он не существует."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Проверяем, существует ли столбец
        cursor.execute("PRAGMA table_info(problems);")
        columns = [info[1] for info in cursor.fetchall()]
        if 'offline_html' not in columns:
            print("Столбец 'offline_html' не найден. Добавляем...")
            cursor.execute("ALTER TABLE problems ADD COLUMN offline_html TEXT;")
            conn.commit()
            print("Столбец 'offline_html' успешно добавлен.")
        else:
            print("Столбец 'offline_html' уже существует.")
    except sqlite3.OperationalError as e:
        print(f"Ошибка при добавлении столбца: {e}")
        conn.close()
        return False
    conn.close()
    return True

def extract_task_content_and_id(html_content: str):
    """
    Извлекает содержимое задачи (.qblock) и суффикс problem_id (data-task-id из .processed_qblock) из HTML-файла блока.

    Возвращает кортеж (task_content, task_id_suffix) или (None, None) в случае ошибки/неудачи.
    """
    # Регулярное выражение для поиска data-task-id в div с class="processed_qblock"
    # (?P<task_id_suffix>...) - именованная группа для захвата суффикса ID
    id_pattern = re.compile(
        r'<div\s+class="processed_qblock"[^>]*\s+data-task-id="(?P<task_id_suffix>[^"]*)"[^>]*>',
        re.IGNORECASE
    )
    id_match = id_pattern.search(html_content)
    if not id_match:
        print("  Не найден data-task-id в .processed_qblock.")
        return None, None

    task_id_suffix = id_match.group('task_id_suffix')

    # Регулярное выражение для поиска внутренностей div с class="qblock"
    # (?P<content>...) - именованная группа для захвата содержимого
    content_pattern = re.compile(
        r'<div\s+class="qblock"[^>]*>(?P<content>.*?)</div>',
        re.DOTALL | re.IGNORECASE
    )
    content_match = content_pattern.search(html_content)
    if not content_match:
        print("  Не найдено содержимое .qblock.")
        return None, None

    task_content = content_match.group('content').strip()
    return task_content, task_id_suffix

def find_problem_id_by_suffix(cursor, task_id_suffix: str):
    """
    Ищет problem_id в базе данных по суффиксу (task_id_suffix).
    Возвращает полный problem_id или None, если не найден.
    """
    # Ищем problem_id, который заканчивается на '_{task_id_suffix}'
    # Например, ищем '_4CBD4E' для суффикса '4CBD4E'
    search_pattern = f'%_{task_id_suffix}'
    cursor.execute("SELECT problem_id FROM problems WHERE problem_id = ? OR problem_id LIKE ?", (task_id_suffix, search_pattern))
    rows = cursor.fetchall()
    # Если найдено несколько, возвращаем первый
    if rows:
        return rows[0][0]
    return None

def migrate_blocks_to_db(db_path: Path, blocks_dir: Path):
    """Основная функция миграции."""
    if not db_path.exists():
        print(f"База данных не найдена: {db_path}")
        return

    if not blocks_dir.exists():
        print(f"Директория с блоками не найдена: {blocks_dir}")
        return

    # Добавляем столбец, если нужно
    if not add_offline_html_column(db_path):
        print("Не удалось добавить столбец offline_html. Прерываю миграцию.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    html_files = list(blocks_dir.glob("block_*.html"))
    print(f"Найдено {len(html_files)} HTML-файлов для обработки.")

    updated_count = 0
    for file_path in html_files:
        print(f"Обрабатываю файл: {file_path.name}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            task_content, extracted_task_id_suffix = extract_task_content_and_id(html_content)

            if not task_content or not extracted_task_id_suffix:
                print(f"  Пропущен: не удалось извлечь содержимое или task_id_suffix из файла.")
                continue

            print(f"  Извлечен суффикс task_id: {extracted_task_id_suffix}")

            # Ищем полный problem_id в БД по суффиксу
            full_problem_id = find_problem_id_by_suffix(cursor, extracted_task_id_suffix)

            if not full_problem_id:
                print(f"  Пропущен: задача с суффиксом task_id '{extracted_task_id_suffix}' не найдена в БД.")
                continue

            print(f"  Сопоставлен полный problem_id: {full_problem_id}")

            # Обновляем offline_html для найденного problem_id
            cursor.execute(
                "UPDATE problems SET offline_html = ? WHERE problem_id = ?",
                (task_content, full_problem_id)
            )
            print(f"  Обновлено поле offline_html для problem_id '{full_problem_id}'.")
            updated_count += 1

        except Exception as e:
            print(f"  Ошибка при обработке файла {file_path.name}: {e}")

    conn.commit()
    conn.close()
    print(f"Миграция завершена. Обновлено {updated_count} записей.")


if __name__ == "__main__":
    print("Запуск скрипта миграции offline_html...")
    migrate_blocks_to_db(DB_PATH, BLOCKS_DIR)
