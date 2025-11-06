# REQ-019: Common Package Usage

## Description
All components of the system (web API, scraping, checking, indexing services) SHALL import shared models, utilities, and services from the `common` package to ensure consistency and avoid code duplication.

## Rationale
To maintain a single source of truth for data models and shared logic, and to facilitate microservice decomposition.

## Acceptance Criteria
- Pydantic models for problems and answers MUST be imported from `common.models.problem_schema` and `common.models.database_models`.
- Shared utility functions (e.g., subject mapping, model conversion) MUST be imported from `common.utils.*`.
- The `SpecificationService` MUST be imported from `common.services.specification`.
- New shared code SHOULD be added to `common` rather than duplicated across components.
- Components SHOULD NOT reimplement functionality already present in `common`.

