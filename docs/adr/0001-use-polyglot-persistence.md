# 1. Use Polyglot Persistence for Multi-Model Data

## Status
Accepted

## Context
The iXe platform is inherently multi-model:
- **Documents**: tasks with rich HTML, metadata, and base64 assets
- **Graphs**: skill dependencies, knowledge tracing, user progress
- **Vectors**: semantic similarity for RAG and adaptive task selection
- **Events**: user interactions (answer submissions, skips)
- **Time-series**: spaced repetition intervals

A single database cannot efficiently support all these models. Forcing one engine (e.g., ArangoDB) to handle vectors, graphs, and documents leads to:
- Suboptimal retrieval quality
- Limited ANN algorithm support
- Poor ecosystem integration (LangChain, LlamaIndex)

## Decision
Adopt **polyglot persistence** with:
- **ArangoDB**: documents + graphs (problems, skills, user progress)
- **Qdrant**: dedicated vector store for embeddings (HNSW, hybrid search)
- **SQLite**: local event logging and temporary state (migratable to PostgreSQL)

This aligns with modern data-intensive architectures and ensures each model uses its optimal storage engine.

## Consequences

### Positive
- High-quality semantic search via Qdrant
- Native graph traversals in ArangoDB
- Simplified local development with SQLite
- Clear migration path to PostgreSQL for events

### Negative
- Increased operational complexity (3 data stores)
- Need for unified domain model across stores
- Additional monitoring and backup procedures

## Alternatives Considered

### a) ArangoDB-only
- Lacks efficient hybrid search (vector + metadata)
- No HNSW tuning or quantization
- Limited RAG ecosystem support

### b) PostgreSQL + pgvector
- Good for vectors, weak for native graphs
- Requires extension management

### c) Qdrant + Neo4j
- Strong specialization, but heavier footprint (JVM)

## References
- [ArangoDB Multi-Model](https://www.arangodb.com/docs/stable/data-modeling-documents-graphs.html)
- [Qdrant Hybrid Search](https://qdrant.tech/documentation/concepts/hybrid-search/)
- [Polyglot Persistence (Martin Fowler)](https://martinfowler.com/bliki/PolyglotPersistence.html)
