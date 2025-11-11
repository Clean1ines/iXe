#!/bin/bash
# Скрипт для коммита изменений с сообщением по индустриальным стандартам

# Проверяем, есть ли изменения
if [[ -z $(git status --porcelain) ]]; then
    echo "Нет изменений для коммита"
    exit 0
fi

# Определяем тип коммита на основе измененных файлов
COMMIT_TYPE="chore"
if git status --porcelain | grep -E "\.(py)$" > /dev/null; then
    COMMIT_TYPE="refactor"
elif git status --porcelain | grep -E "(Makefile|Docker|docker-compose|requirements)" > /dev/null; then
    COMMIT_TYPE="build"
elif git status --porcelain | grep -E "\.(yml|yaml)$" > /dev/null; then
    COMMIT_TYPE="ci"
fi

# Добавляем все изменения
git add .

# Генерируем сообщение коммита
COMMIT_MSG="${COMMIT_TYPE}(devops): add CI/CD automation and stable test execution"

# Добавляем описание
COMMIT_DESC="
- Add Makefile for standardized development workflow
- Add docker-compose.yml for local multi-container setup
- Update CI workflow to run stable tests only
- Add pre-commit hook for stable test execution
- Add run_stable_tests.sh script for selective test running
- Update various adapters and services for clean architecture
- Refactor database and infrastructure adapters
- Add skill graph and vector indexing utilities
- Update API dependencies and endpoints for new architecture
- Include subject mapping and model adapter improvements
"

# Совершаем коммит
git commit -m "$COMMIT_MSG" -m "$COMMIT_DESC"

echo "Коммит создан: $COMMIT_MSG"
