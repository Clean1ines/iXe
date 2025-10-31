# FIPI Specification Integration Guide

## Official Sources
- `data/specs/ege_2026_math_spec.json` — Exam blueprint (tasks 1–19)
- `data/specs/ege_2026_math_kes_kos.json` — KES/KOS code definitions

## Key Mappings
| Field | Source | Example |
|-------|--------|---------|
| `task_number` | `spec.json` | `18` |
| `kes_codes` | `spec.json` | `["2.3", "4.1"]` |
| `kos_codes` | `spec.json` | `["3"]` |
| `kes_description` | `kes_kos.json` | `"2.3 — Тригонометрические уравнения"` |
| `kos_description` | `kes_kos.json` | `"Умение решать уравнения с параметром"` |

## Usage Examples

### 1. Get feedback for task 18
```python
from services.specification import SpecificationService
spec = SpecificationService(...)
feedback = spec.get_feedback_for_task(18)
# → kos_explanation: "Умение решать уравнения с параметром (КОС 3)"
```

### 2. Validate scraped problem
```python
assert problem.task_number in range(1, 20)
assert all(kes in known_kes_codes for kes in problem.kes_codes)
```

### 3. Generate Part 2 quiz
```python
part2_tasks = [t for t in spec["tasks"] if t["exam_part"] == "Part 2"]
```

## Validation Rules
- Every `Problem` must have `task_number` ∈ [1, 19]
- All `kes_codes` must exist in `kes_kos.json`
- `max_score` must match spec (e.g., task 19 → 4 points)

## References
- [FIPI Official Site](https://fipi.ru/ege/)
- [SpecificationService](../../services/specification.py)
