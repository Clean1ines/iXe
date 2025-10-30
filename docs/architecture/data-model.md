# Unified Data Model Strategy

## Overview
iXe is a **multi-model system** by design. No single database can optimally serve all data access patterns. Instead, we maintain a **unified domain model** in code, mapped to specialized storage engines.

## Domain Entities
| Entity | Description | Primary Store |
|--------|-------------|---------------|
| `Problem` | Task from FIPI with text, options, solutions, metadata | ArangoDB (document) |
| `Skill` | Atomic knowledge unit (e.g., "solve quadratic equations") | ArangoDB (document) |
| `UserProgress` | Mastery state per skill | ArangoDB (graph edges) |
| `Embedding` | Vector representation of problem text | Qdrant |
| `UserEvent` | Timestamped interaction (answer, skip, etc.) | Kafka → ArangoDB + Analytics |
| `StudyPlan` | Generated sequence of tasks | ArangoDB (document) |

## Storage Mapping
| Model Type | Use Case | Storage Engine | Rationale |
|-----------|----------|----------------|----------|
| **Document** | Rich task content, metadata | ArangoDB | Flexible schema, ACID, embeddable |
| **Graph** | Skill dependencies, knowledge tracing | ArangoDB | Native traversals, pathfinding |
| **Vector** | Semantic similarity, RAG | Qdrant | HNSW, hybrid search, payload filtering |
| **Event Stream** | Audit log, real-time processing | Kafka/Redpanda | Durability, replay, consumer groups |
| **Time-Series** | Spaced repetition intervals | ArangoDB (temporary) → TimescaleDB | Temporal queries, retention policies |

## Cross-Store Consistency
- **Ingestion pipeline** is the source of truth:
  1. Scraper → `Problem` object
  2. Publish to ArangoDB (document + graph edges)
  3. Generate embedding → publish to Qdrant
  4. Emit `problem_ingested` event to Kafka
- **No distributed transactions** — eventual consistency via idempotent writes

## Future Evolution
- Replace SQLite `DBAnswer` with Kafka-sourced state
- Add TimescaleDB for high-cardinality time-series (e.g., per-user response times)
- Introduce materialized views for dashboard queries

## Official FIPI Specifications Integration

The system ingests two authoritative JSON documents from FIPI:

1. **`ege_2026_math_spec.json`** — Exam blueprint:
   - Maps task numbers (1–19) to KES/KOS codes
   - Defines difficulty, max score, exam part
   - Serves as the source of truth for quiz generation

2. **`ege_2026_math_kes_kos.json`** — Code definitions:
   - Full human-readable descriptions of every KES (content element) and KOS (requirement)
   - Enables explainable feedback: "You missed KOS 3: solving equations with parameters"

These documents are loaded at startup by `SpecificationService` and used to:
- Validate scraped problems against official taxonomy
- Generate adaptive study plans aligned with exam structure
- Provide pedagogically meaningful error explanations

- **Document Collection**: `specifications`
  - Key: `math_2026`
  - Contains full `ege_2026_math_spec.json` and `kes_kos` mapping
  - Used by `SpecificationService` for validation and feedback

## References
- [ADR-0001: Polyglot Persistence](../adr/0001-use-polyglot-persistence.md)
- [ADR-0002: Migrate to ArangoDB](../adr/0002-migrate-to-arangodb.md)
- [ADR-0003: Introduce Kafka](../adr/0003-introduce-kafka-for-event-streaming.md)
