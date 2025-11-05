# iXe — Personalized ЕГЭ Preparation Platform

> **Standards-aligned adaptive tutor** for ЕГЭ (Unified State Exam) in Mathematics, Informatics, and Russian Language.

Built on **official FIPI specifications** (КЭС/КОС 2026) and **multi-model architecture**.

## ✨ Features
- **Official task bank**: Scraped from [fipi.ru](https://ege.fipi.ru/bank/    )
- **Pedagogical feedback**: "You missed KOS 3: solving equations with parameters"
- **Offline-first PWA**: Works on iPhone XR, supports Telegram Mini App
- **Adaptive quizzes**: Based on skill graph (planned) and vector similarity (Qdrant)
- **Exam-structure compliant**: Part 1 (12 tasks) / Part 2 (7 tasks), scoring, difficulty

## 🏗️ Architecture Status
| Component | Status | Tech |
|----------|--------|------|
| Scraping | ✅ Stable | Playwright + SQLAlchemy |
| API | ✅ Stable | FastAPI |
| Frontend | ✅ Stable | React + Vite |
| Common Library | ✅ Stable | Pydantic, SQLAlchemy |

## 🌐 Demo
- **Frontend**: [ixe.onrender.com](https://ixe.onrender.com    )
- **API Docs**: [ixe-core.onrender.com/docs](https://ixe-core.onrender.com/docs    )

## 🧱 Common Library
Проект использует общую библиотеку `common`, расположенную в директории `common/`. Она содержит общие модели данных, утилиты и логику, используемые различными частями приложения (API, скрапер, скрипты).

Для корректной работы проекта необходимо установить `common` как редактируемый пакет:

```bash
make install-common
```

или вручную:

```bash
pip install -e common/
```

## 🚀 Development
```bash
# Setup common library
make install-common

# Backend
python run.py

# Frontend
cd frontend && npm run dev
```

## 🛠️ Development Commands

### Installing Dependencies
- `make install-dev`: Install development tools (pytest, black, mypy, etc.)
- `make install-common`: Install common library in editable mode
- `make install-web`: Install web API dependencies and common library
- `make install-scraping-checking`: Install scraping and checking service dependencies and common library
- `make install-indexing`: Install indexing service dependencies and common library

### Dependency Analysis
- `make analyze-deps-api`: Analyze dependencies for the API component
- `make analyze-deps-scraper`: Analyze dependencies for the scraper component
- `make analyze-deps-checker`: Analyze dependencies for the answer checker component
- `make analyze-deps-indexer`: Analyze dependencies for the indexer component
- `make analyze-deps-common`: Analyze dependencies for the common library

### Testing
- `make test-reqs`: Run tests for requirements files

