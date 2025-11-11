# Makefile для проекта FIPI Parser
# Предоставляет стандартные цели для установки зависимостей, запуска, тестирования и форматирования

.PHONY: install run test test-stable format check deploy help

# Установка зависимостей из requirements.txt
install:
	pip install -r requirements.txt

# Запуск основного приложения
run:
	python -m main

# Запуск всех тестов (включая падающие) с подробным выводом
test:
	pytest -xvs

# Запуск только стабильных тестов
test-stable:
	bash scripts/run_stable_tests.sh

# Форматирование кода с помощью black и isort
format:
	black .
	isort .

# Проверка кода с помощью flake8 и mypy
check:
	flake8 .
	mypy .

# Заглушка для цели деплоя (требует реализации)
deploy:
	@echo "Deploy logic goes here"

# Вывод справки по доступным целям
help:
	@echo "Доступные цели:"
	@echo "  install     - Установить зависимости"
	@echo "  run         - Запустить приложение"
	@echo "  test        - Запустить все тесты"
	@echo "  test-stable - Запустить только стабильные тесты"
	@echo "  format      - Отформатировать код"
	@echo "  check       - Проверить код (flake8, mypy)"
	@echo "  deploy      - Деплой приложения (реализация зависит от окружения)"
	@echo "  help        - Показать это сообщение"
