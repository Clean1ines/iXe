#!/bin/bash
set -e # Прервать при ошибке

echo "Запуск миграции offline_html..."
# Убедимся, что скрипт запускается из корня проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Проверим, что директории существуют
if [ ! -d "frontend/public/blocks/math" ]; then
  echo "Директория frontend/public/blocks/math не найдена. Проверьте структуру проекта."
  exit 1
fi

if [ ! -f "data/math/fipi_data.db" ]; then
  echo "Файл базы данных data/math/fipi_data.db не найден. Проверьте структуру проекта."
  exit 1
fi

python scripts/migrate_offline_html.py

if [ $? -eq 0 ]; then
    echo "Миграция offline_html успешно выполнена."
else
    echo "Ошибка при выполнении миграции offline_html."
    exit 1
fi

echo "Все миграции выполнены."
