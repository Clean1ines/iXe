# 4. Use Official FIPI Specifications as Source of Truth

## Status
Accepted

## Context
The platform scrapes tasks from fipi.ru, but without alignment to the official exam blueprint, it cannot:
- Guarantee coverage of all KES/KOS codes
- Provide meaningful feedback tied to exam requirements
- Generate valid mock exams (e.g., "Part 1: 12 tasks, max 12 points")

FIPI publishes machine-readable specifications for ЕГЭ 2026, including:
- Task-to-KES/KOS mapping
- Difficulty and scoring rules
- Full code definitions

## Decision
Treat `ege_2026_math_spec.json` and `ege_2026_math_kes_kos.json` as **authoritative sources** for:
- Problem validation during scraping
- Adaptive quiz generation
- User feedback and study plan recommendations

A `SpecificationService` will load these files at startup and expose methods to:
- Get task metadata by number
- Explain KOS/KES codes in natural language
- Validate problem completeness (required fields: task_number, kes_codes, etc.)

## Consequences

### Positive
- 100% alignment with official ЕГЭ structure
- Pedagogically sound feedback ("You need to master KOS 3")
- Foundation for mock exam mode

### Negative
- Tight coupling to FIPI's JSON format
- Requires update when FIPI changes spec (annual)

## Validation
- [ ] All scraped problems have `task_number` matching spec
- [ ] All `kes_codes` exist in `kes_kos` mapping
- [ ] Quiz generator respects `exam_part` and `max_score`

## References
- FIPI ЕГЭ 2026 Specification (internal JSON files)
- [FIPI Official Site](https://fipi.ru/ege/... )
