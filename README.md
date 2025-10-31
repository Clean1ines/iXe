
# iXe — Personalized ЕГЭ Preparation Platform

> **Standards-aligned adaptive tutor** for ЕГЭ (Unified State Exam) in Mathematics, Informatics, and Russian Language.

Built on **official FIPI specifications** (КЭС/КОС 2026) and **multi-model architecture**.

## ✨ Features
- **Official task bank**: Scraped from [fipi.ru](https://ege.fipi.ru/bank/)
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
| Skill Graph | 🚧 Planned | ArangoDB |
| Event Streaming | 🚧 Planned | Kafka/Redpanda |
| Specification Service | ✅ Stable | FIPI JSON |

## 🌐 Demo
- **Frontend**: [ixe.onrender.com](https://ixe.onrender.com)
- **API Docs**: [ixe-core.onrender.com/docs](https://ixe-core.onrender.com/docs)

## 📚 Documentation
- [Architecture Overview](docs/architecture/overview.md)
- [Domain & Storage Model](docs/architecture/domain-and-storage.md)
- [FIPI Specification Integration](docs/data/fipi-spec-integration.md)
- [ADR: Polyglot Persistence](docs/adr/0001-use-polyglot-persistence.md)
- [OpenAPI Spec](docs/api/openapi.yaml)

## 🚀 Development
```bash
# Backend
python run.py

# Frontend
cd frontend && npm run dev
