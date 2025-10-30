# iXe — Personalized ЕГЭ Preparation Platform

An adaptive learning system for ЕГЭ (Unified State Exam) in Mathematics, Informatics, and Russian Language.

## Features
- Scraping of official FIPI tasks
- Offline-first PWA with Telegram Mini App support
- Skill-based knowledge tracing (planned)
- Semantic task retrieval via vector search (Qdrant)
- Adaptive quiz generation

## Architecture
- **Frontend**: React + Vite → [ixe.onrender.com](https://ixe.onrender.com)
- **Backend**: FastAPI → [ixe-core.onrender.com](https://ixe-core.onrender.com)
- **Storage**: Polyglot persistence (ArangoDB + Qdrant + SQLite)

## Documentation
- [Architecture Overview](docs/architecture/overview.md)
- [ADR: Polyglot Persistence](docs/adr/0001-use-polyglot-persistence.md)
- [API Specification](docs/api/openapi.yaml)
- Interactive Swagger UI: [`/docs`](https://ixe-core.onrender.com/docs)

## Development
```bash
# Backend
python run.py

# Frontend
cd frontend && npm run dev\nLicense
Proprietary — for educational use only.
