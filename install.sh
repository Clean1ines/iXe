#!/bin/bash

# install.sh
# Скрипт для установки зависимостей проекта FIPI Parser

set -e # Прекращает выполнение при ошибке

echo "=== Установка зависимостей для FIPI Parser ==="

# Проверка наличия Python 3
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python 3 не найден. Установите Python 3."
    exit 1
fi

# Проверка наличия pip
if ! command -v pip3 &> /dev/null; then
    echo "Ошибка: pip3 не найден. Убедитесь, что pip установлен вместе с Python."
    exit 1
fi

echo "Найден Python: $(python3 --version)"
echo "Найден Pip: $(pip3 --version)"

# Установка FastAPI и Uvicorn (для запуска сервера)
echo "Устанавливаем FastAPI и Uvicorn..."
pip3 install "fastapi[all]" uvicorn

# Установка httpx (для асинхронных HTTP-запросов в checker)
echo "Устанавливаем httpx..."
pip3 install httpx

# Установка pytest (для тестирования)
echo "Устанавливаем pytest..."
pip3 install pytest

# Установка дополнительных зависимостей, если необходимо (например, для запуска playwright)
# pip3 install playwright
# playwright install # Для установки браузеров

echo "=== Установка завершена ==="
echo "Теперь вы можете запустить API сервер с помощью команды:"
echo "uvicorn api.answer_api:app --reload --host 0.0.0.0 --port 8000"
echo "Или выполнить тесты командой:"
echo "python3 -m pytest tests/"
