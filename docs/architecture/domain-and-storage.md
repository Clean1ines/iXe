# Domain Model and Storage Strategy

## Overview

iXe is a **multi-model educational platform** built around the official FIPI ЕГЭ 2026 specifications.  
The system maintains a **unified domain model** in code, mapped to specialized storage engines based on data access patterns.

This document describes:
- Core domain entities and their relationships
- Mapping to physical storage (ArangoDB, Qdrant, Kafka, SQLite)
- Integration with official FIPI specifications (КЭС/КОС)

---

## Domain Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| `Problem` | Task scraped from FIPI with full metadata | `problem_id`, `task_number`, `kes_codes`, `kos_codes`, `offline_html`, `difficulty_level`, `max_score` |
| `Skill` | Atomic knowledge unit from FIPI codifier | `skill_id` (e.g., `"2.3"`), `description` |
| `UserProgress` | Mastery state per skill per user | `user_id`, `skill_id`, `mastery_level`, `last_practiced` |
| `Embedding` | Vector representation of problem text | `vector` (768-dim), `problem_id`, `payload` |
| `UserEvent` | Timestamped interaction (answer, skip, etc.) | `event_id`, `user_id`, `problem_id`, `event_type`, `timestamp` |
| `StudyPlan` | Sequence of tasks for adaptive learning | `plan_id`, `user_id`, `tasks[]`, `target_date` |

---

## FIPI Specification Integration

The platform is grounded in two authoritative JSON documents:

1. **`ege_2026_math_spec.json`** — Exam blueprint  
   - Maps `task_number` (1–19) → `kes_codes`, `kos_codes`, `max_score`, `exam_part`
   - Defines official difficulty levels: `basic`, `advanced`, `high`

2. **`ege_2026_math_kes_kos.json`** — Code definitions  
   - Provides human-readable descriptions for every КЭС and КОС  
   - Enables pedagogical feedback:  
     > _"You missed KOS 3: solving equations with parameters"_

These documents are loaded at startup by `SpecificationService` and used to:
- Validate scraped problems against the official taxonomy
- Generate exam-structure-compliant quizzes (Part 1 / Part 2)
- Provide explainable error feedback tied to official requirements

### Example Mapping

| Field | Source | Example |
|------|--------|---------|
| `task_number` | `spec.json` | `18` |
| `kes_codes` | `spec.json` | `["2.3", "4.1"]` |
| `kos_codes` | `spec.json` | `["3"]` |
| `kes_description` | `kes_kos.json` | `"2.3 — Тригонометрические уравнения"` |
| `kos_description` | `kes_kos.json` | `"Умение решать уравнения с параметром"` |

---

## Storage Strategy

| Data Model | Use Case | Storage Engine | Rationale |
|-----------|----------|----------------|----------|
| **Document** | Rich task content, metadata, HTML | **ArangoDB** | Flexible schema, ACID, embeddable documents |
| **Graph** | Skill dependencies, knowledge tracing | **ArangoDB** | Native graph traversals, pathfinding, AQL |
| **Vector** | Semantic similarity, RAG, task retrieval | **Qdrant** | HNSW indexing, hybrid search, payload filtering |
| **Event Stream** | Audit log, real-time analytics | **Kafka/Redpanda** | Durability, replay, consumer groups |
| **Time-Series** | Spaced repetition intervals, response times | **ArangoDB → TimescaleDB** | Temporal queries, retention policies |

> **Note**: SQLite is used **only for local development** (answers, problems). Production will migrate to ArangoDB + Kafka.

---

## Cross-Store Consistency

The **ingestion pipeline** is the single source of truth:

1. **Scraper** → produces `Problem` object with `task_number`, `kes_codes`, etc.
2. **Validator** → ensures compliance with `ege_2026_math_spec.json`
3. **Publisher** → writes to:
   - ArangoDB (`problems`, `skills`, `problem_skills` edges)
   - Qdrant (embedding + payload)
   - Kafka (`problem_ingested` event)

**No distributed transactions** — eventual consistency via idempotent writes and replayable event log.

---

## Future Evolution

- Replace SQLite `DBAnswer` with Kafka-sourced state in ArangoDB
- Add TimescaleDB for high-cardinality time-series (e.g., per-user response latency)
- Introduce materialized views for dashboard queries (e.g., "mastery by КЭС")

---

## References

- [ADR-0001: Polyglot Persistence](../adr/0001-use-polyglot-persistence.md)
- [ADR-0002: Migrate to ArangoDB](../adr/0002-migrate-to-arangodb.md)
- [ADR-0003: Introduce Kafka](../adr/0003-introduce-kafka-for-event-streaming.md)
- [ADR-0004: Use Official FIPI Specifications](../adr/0004-use-official-fipi-specifications.md)
- [FIPI Specification Guide](../data/fipi-spec-integration.md)
