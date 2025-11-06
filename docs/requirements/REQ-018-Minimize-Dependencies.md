# REQ-018: Minimize Dependencies

## Description
Each component of the system (web API, scraping, checking, indexing) SHALL include only the minimal set of external dependencies required for its specific functionality.

## Rationale
To reduce the overall size of the application, improve security, and simplify dependency management.

## Acceptance Criteria
- Heavy dependencies (e.g., `playwright`, `qdrant-client`, `selenium`) MUST NOT be included in `requirements_web.txt`.
- Common code MUST be extracted into the `common/` package to avoid duplication and unnecessary dependencies in individual components.
- The `audit_requirements.py` script MUST be used periodically to identify and remove unused dependencies from all `requirements_*.txt` files.

