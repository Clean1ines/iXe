# Dependency Management

This document outlines how dependencies are managed in the project, including the `common` package and the microservice architecture.

## Requirements Files

The project uses multiple `requirements.txt` files to manage dependencies for different components:

- `requirements.txt`: The original, monolithic file (may be deprecated).
- `requirements_web.txt`: Dependencies for the FastAPI web API service. **Excludes heavy dependencies like `playwright`, `qdrant-client`.**
- `requirements_scraping_checking.txt`: Dependencies for the scraping and answer checking service (e.g., `playwright`, `requests`, `beautifulsoup4`).
- `requirements_indexing.txt`: Dependencies for the indexing service (e.g., `qdrant-client`, `sentence-transformers`).
- `requirements_common.txt`: Dependencies specifically for the `common` package itself (e.g., `pydantic`, `sqlalchemy`).
- `dev-requirements.txt`: Development dependencies (e.g., `pytest`, `black`, `mypy`).

## Managing Common Package Dependencies

The `common/` package has its own dependencies defined in `common/setup.py`. When you install the common package using `pip install -e ./common`, it will automatically install the dependencies listed in `setup.py`.

- To add a new dependency required by code inside `common/`, add it to the `install_requires` list in `common/setup.py`.
- Do NOT add `common`'s internal dependencies (like `pydantic` if already used elsewhere) to the component-specific `requirements_*.txt` files unless the component uses that package *directly* and *independently* of `common`.
- The `requirements_common.txt` file serves as a human-readable summary of `common`'s direct dependencies.

## Managing Microservice Dependencies

Each microservice (Web API, Scraping/Checking, Indexing) has its own `requirements_*.txt` file. This file should contain only the dependencies required by that specific service's core logic, *excluding* the dependencies of the `common` package itself (as these are pulled in via `pip install -e ./common`).

- When adding a dependency, first consider if it's specific to the service's unique logic or if it's shared (and thus should go in `common/setup.py`).
- Add service-specific dependencies to the corresponding `requirements_*.txt` file.
- Update the service's Dockerfile to install from its specific `requirements_*.txt` and install `common`.

## Verification

Use the `audit_requirements.py` script to analyze the codebase and verify that the dependencies listed in the `requirements_*.txt` files match the actual imports used by each component. This helps ensure the separation is maintained and identifies unused dependencies.

