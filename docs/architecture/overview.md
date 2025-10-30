# System Architecture

## Overview
iXe is a personalized ЕГЭ preparation platform that combines:
- Web scraping of official FIPI tasks
- Adaptive quiz delivery via PWA (Telegram Mini App compatible)
- Skill-based knowledge tracing
- Offline-first content rendering

## High-Level Components

```mermaid
graph LR
  A[PWA Frontend] -->|HTTPS| B(FastAPI Core)
  B --> C[(ArangoDB)]
  B --> D[(Qdrant)]
  B --> E[(SQLite)]
  F[FIPI Scraper] -->|ingest| C
  F -->|embed| D Data Flow
User selects subject → GET /api/subjects/available
System generates quiz → POST /api/quiz/{subject}/start
Answers submitted → POST /api/answer → checked via FIPIAnswerChecker
Skill graph updated in ArangoDB (future)
Next task selected via rule engine + vector similarity (Qdrant)
Deployment
Frontend: React PWA, hosted as Static Site on Render (ixe.onrender.com)
Backend: FastAPI on Render Web Service (ixe-core.onrender.com)
Storage:
fipi_data.db: pre-scraped tasks (read-only in prod)
ArangoDB: skill graph (planned)
Qdrant: embeddings for semantic search
Scraping: local-only (Playwright)
Key Design Principles
Offline-first: all task content embeddable as data URI
Stateless API: no session storage; user state derived from DB
Testability: all core logic dependency-injected
Extensibility: subject-agnostic API design
Future Directions
Replace SQLite with ArangoDB for skill graph
Add RAG pipeline: user question → Qdrant → ArangoDB → explanation
Implement spaced repetition scheduler
