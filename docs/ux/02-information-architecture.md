# Information Architecture: EGÉ Preparation Platform

## Core Data Models
- **`Problem`** (`common/models/problem_schema.py`): Represents an EGÉ task with ID, subject, text, offline HTML, KES/KOS codes, topics, etc. Used by all services.
- **`DBProblem`** (`common/models/database_models.py`): SQLAlchemy ORM model for storing `Problem` in the database. Used by all services accessing the DB.
- **`DBAnswer`** (`common/models/database_models.py`): SQLAlchemy ORM model for storing user answers and statuses. Used by Web API and potentially other services.
- **`Specification`** (`common/services/specification.py`): Represents official EGÉ KES/KOS data. Used by Web API for feedback generation.

## System Components & Information Flow (Microservice View)
- **Scraping & Checking Service**:
  - **`scraper/`**: Extracts raw data from FIPI, constructs `Problem` objects (using `common/models/problem_schema.py`), saves to database (`DBProblem` via `utils/database_manager.py` which uses `common/models/database_models.py`).
- **Indexing Service**:
  - **`utils/vector_indexer.py`**: Fetches `Problem` data from DB (`DBProblem`), generates embeddings, stores in Qdrant. Uses `common/models/problem_schema.py`.
- **Web API Service**:
  - **`api/`**: Exposes endpoints for quiz generation and answer checking.
    - **`api/services/quiz_service_adapter.py`**: Selects problems using database data (`Problem` schema from `common`), potentially using `InMemorySkillGraph` (`utils/skill_graph.py`).
    - **`api/services/answer_service.py`**: Processes answers, validates using `FIPIAnswerChecker` (`utils/answer_checker.py` - potentially calls Scraping&Checking service), updates database (`utils/database_manager.py`), generates feedback using `SpecificationService` (`common/services/specification.py`).

## User-Facing Information
- **Quiz Items** (`api/schemas.py`): Derived from `Problem` schema (`common/models/problem_schema.py`) for API responses.
- **Feedback** (`api/schemas.py`, `common/services/specification.py`): Generated based on official specifications and user performance.
- **Progress Tracking** (`utils/skill_graph.py`): Internal representation based on `DBAnswer` and `Specification` data.

## Common Library Role
The `common/` package centralizes shared data definitions (`models`), business rules (`services/specification.py`), and stateless utilities (`utils`). This ensures data consistency and reduces duplication across the Scraping & Checking, Indexing, and Web API services.

