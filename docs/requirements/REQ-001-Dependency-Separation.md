# REQ-001: Dependency Separation

## Description
The system SHALL separate its Python dependencies into distinct files based on the functional component that uses them (web API, scraping, checking, indexing) to minimize memory footprint and ensure compliance with platform limitations (e.g., Render Free tier).

## Rationale
To avoid Out of Memory errors on constrained environments and improve modularity.

## Acceptance Criteria
- There MUST be a `requirements_web.txt` containing only dependencies required by the web API service.
- There MUST be a `requirements_scraping_checking.txt` containing dependencies required by the scraping and answer checking services.
- There MUST be a `requirements_indexing.txt` containing dependencies required by the indexing service.
- The web API service MUST NOT load dependencies specific to scraping or indexing (e.g., `playwright`, `qdrant-client`).
- A script (`audit_requirements.py`) MUST exist to verify the separation and report discrepancies.

