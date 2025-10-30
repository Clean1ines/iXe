# 3. Introduce Kafka for Event Streaming

## Status
Proposed

## Context
The system currently stores user interactions (answer submissions, skips, time spent) in SQLite (`DBAnswer`). This approach:
- Limits scalability to single-user scenarios
- Prevents real-time analytics (e.g., session replay, anomaly detection)
- Makes it hard to implement event-driven features (e.g., "notify user after 3 incorrect attempts")

As iXe evolves toward multi-user support and adaptive interventions, a durable, ordered event log is required.

## Decision
Introduce **Apache Kafka** (or Redpanda for lightweight alternative) as the event streaming backbone:

- All user actions → published to `user_events` topic
- Consumers:
  - **State updater**: writes to ArangoDB (user progress graph)
  - **Analytics pipeline**: logs to ClickHouse or file
  - **Notification service**: triggers Telegram alerts

### Event Schema (JSON)
```json
{
  "event_id": "uuid4",
  "user_id": "default_user",
  "event_type": "answer_submitted",
  "problem_id": "init_4CBD4E",
  "payload": {
    "user_answer": "42",
    "verdict": "correct",
    "time_spent_sec": 15
  },
  "timestamp": "2025-10-31T12:00:00Z"
} Deployment
Local dev: Redpanda (Docker, single node)
Production: Managed Kafka (e.g., AWS MSK, Confluent Cloud)
Consequences
Positive
Decouples event production from consumption
Enables real-time and batch processing
Provides audit trail for all user interactions
Scales to millions of events
Negative
Adds operational complexity (Kafka cluster)
Requires schema registry for evolution (optional in MVP)
Increases latency for state updates (async)
Alternatives Considered
a) Keep SQLite events
Works for solo use, but blocks multi-user and analytics
b) Use PostgreSQL with LISTEN/NOTIFY
Limited throughput, no replay semantics
c) Write to files (JSONL)
Simple, but no ordering, no consumer groups
Next Steps
Evaluate Redpanda vs Kafka for local development
Prototype event publisher in FIPIAnswerChecker
Design consumer for ArangoDB state updates
References
ADR-0001: Polyglot Persistence
Kafka Event Sourcing Patterns
