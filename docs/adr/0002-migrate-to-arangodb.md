# 2. Migrate Problem and Skill Storage to ArangoDB

## Status
Proposed

## Context
The current SQLite-based storage (`DBProblem`, `DBAnswer`) treats problems as flat documents. However, the iXe platform requires:
- Modelling explicit relationships between problems, skills, and user progress
- Traversing skill dependency graphs (e.g., "task 15 requires mastery of skills A → B → C")
- Supporting adaptive learning paths based on graph reachability
- Enabling multi-hop queries (e.g., "find all problems that test skill X and are similar to problem Y")

SQLite lacks native graph capabilities. While JSON fields can store skill lists, they do not support:
- Efficient graph traversals
- ACID-compliant updates across related entities
- Pathfinding or dependency resolution

ArangoDB was selected in ADR-0001 as the primary store for documents and graphs. This ADR proposes the concrete migration plan.

## Decision
Migrate `DBProblem` and skill metadata from SQLite to ArangoDB using the following model:

### Data Model
- **Document Collection**: `problems`
  - Each document = `Problem` (as defined in `problem_schema.py`)
  - Key: `problem_id`
- **Document Collection**: `skills`
  - Each document = skill definition (e.g., `{"_key": "algebra.equations", "name": "Linear equations", "level": "basic"}`)
- **Edge Collection**: `problem_skills`
  - `_from`: `problems/problem_id`
  - `_to`: `skills/skill_id`
- **Edge Collection**: `skill_dependencies`
  - `_from`: `skills/prerequisite_id`
  - `_to`: `skills/skill_id`

### Migration Strategy
1. **Phase 1**: Dual-write — save problems to both SQLite and ArangoDB
2. **Phase 2**: Read from ArangoDB for graph-aware features; fallback to SQLite otherwise
3. **Phase 3**: Decommission SQLite for problem storage (retain for `DBAnswer` events)

### Implementation Steps
- Add `ArangoDBManager` with methods:
  - `save_problem(problem: Problem)`
  - `get_problems_by_skill(skill_id: str, depth: int = 1)`
  - `get_skill_graph(user_id: str)`
- Update `FIPIScraper` to write to ArangoDB during ingestion
- Update API endpoints to use ArangoDB for `/api/quiz/...` generation

## Consequences

### Positive
- Native support for skill-based adaptive learning
- ACID transactions over graph structures
- Unified storage for documents and relationships
- Foundation for spaced repetition based on skill gaps

### Negative
- Adds ArangoDB as a required dependency in development
- Increases complexity of data pipeline
- Requires learning AQL and ArangoDB deployment patterns

## Alternatives Considered

### a) Keep SQLite + in-memory graph
- Simple, but does not persist graph state; unsuitable for production

### b) Use Neo4j
- Strong graph model, but JVM-based, heavier footprint, licensing complexity

### c) Extend Qdrant with metadata
- Possible for flat tags, but cannot express transitive dependencies

## Validation Criteria
- [ ] ArangoDB instance runs locally via Docker
- [ ] Problem ingestion populates `problems` and `problem_skills`
- [ ] AQL query returns all problems for a given skill
- [ ] Skill dependency path is traversable (e.g., A → B → C)

## References
- [ADR-0001: Polyglot Persistence](0001-use-polyglot-persistence.md)
- [ArangoDB Graph Documentation](https://www.arangodb.com/docs/stable/graphs.html)
- FIPI skill taxonomy (internal)
