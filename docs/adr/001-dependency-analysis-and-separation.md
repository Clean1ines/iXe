# 001: Dependency Analysis and Separation for Render Free Tier Compliance

## Status
Accepted

## Context
The application faced Out of Memory (OOM) errors on Render's Free tier. This was primarily due to the monolithic `requirements.txt` containing heavy dependencies like `playwright` and `qdrant-client` being loaded even for lightweight API calls. Additionally, there was significant code duplication across components (scraper, API, indexer) for models, database handling, and utility functions, making maintenance difficult and increasing the overall codebase size.

## Decision
We decided to:
1.  Analyze the codebase to identify which external dependencies are used by which components (web API, scraper, checker, indexer).
2.  Separate the monolithic `requirements.txt` into component-specific files:
    *   `requirements_web.txt`: Minimal dependencies for the FastAPI web service (e.g., `fastapi`, `uvicorn`, `pydantic`).
    *   `requirements_scraping_checking.txt`: Dependencies for scraping and answer checking (e.g., `playwright`, `requests`, `beautifulsoup4`).
    *   `requirements_indexing.txt`: Dependencies for vector indexing (e.g., `qdrant-client`, `sentence-transformers`).
3.  Introduce a `common/` package to house shared components:
    *   Shared Pydantic models (`common/models/problem_schema.py`).
    *   Shared SQLAlchemy models (`common/models/database_models.py`).
    *   Shared utility functions (`common/utils/`).
    *   Shared services like `SpecificationService` (`common/services/specification.py`).
4.  Use `pip install -e ./common` to install the common package in an editable way, allowing components to import shared code.
5.  Create a dedicated `audit_requirements.py` script to automate the analysis of imports and verify the separation.

## Consequences
### Positive:
- **Reduced Memory Footprint**: Each service only loads its specific dependencies, significantly reducing memory usage for individual components, especially the web API. This allows the web API service to run on Render's Free tier.
- **Improved Modularity**: Clear separation of concerns between different parts of the application.
- **Enhanced Maintainability**: Centralized common code reduces duplication and makes updates easier.
- **Scalability**: Easier to scale individual components independently based on their specific requirements.
- **Faster Deployments**: Smaller, focused Docker images for each service.

### Negative:
- **Increased Complexity**: Managing multiple requirements files and a separate `common` package adds initial setup and maintenance overhead.
- **Dependency Management**: Care must be taken to manage dependencies within `common` and avoid introducing heavy dependencies that would defeat the purpose of separation.
- **Learning Curve**: New contributors need to understand the multi-file requirements structure and the `common` package.

