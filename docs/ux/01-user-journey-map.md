# User Journey Map: EGÉ Preparation Platform

## Goal: Successfully complete an adaptive quiz and receive feedback

### 1. Onboarding & Goal Setting
- **User Action:** User visits the platform, creates an account, selects subject (e.g., "Mathematics"), and specifies goal (e.g., "Prepare for EGÉ").
- **System Response:** Presents available study paths or quiz types (e.g., "Daily Quiz", "Calibration Quiz", "Topic Practice").
- **Cognitive Technique:** **Elaborative Interrogation** - System might prompt user to articulate their current confidence level in specific topics.
- **Component:** `api/endpoints/subjects.py`, `common/models/problem_schema.py` (for subject data).

### 2. Engaging with Content
- **User Action:** User selects "Daily Quiz".
- **System Response:** `QuizServiceAdapter` (using data from `DatabaseManager` and potentially adaptive logic from `InMemorySkillGraph` via `common`) selects a set of problems. Problems are rendered with offline HTML (`Problem.offline_html` from `common/models/problem_schema.py`).
- **Cognitive Technique:** **Spaced Repetition**, **Retrieval Practice** - Problems are selected based on user's history and difficulty to promote long-term retention.
- **Component:** `api/endpoints/quiz.py`, `api/services/quiz_service_adapter.py`, `utils/database_manager.py`, `utils/skill_graph.py`, `common/models/problem_schema.py`.

### 3. Submitting an Answer
- **User Action:** User inputs their answer into the interactive form.
- **System Response:** The answer is sent to the API endpoint.
- **Component:** Frontend (React/Vue), `api/endpoints/answer.py`.

### 4. Receiving Feedback
- **User Action:** User submits the answer.
- **System Response:** `AnswerService` (using `FIPIAnswerChecker`, `DatabaseManager`, `LocalStorage`, `InMemorySkillGraph`, `SpecificationService`) validates the answer, generates feedback based on KES/KOS (`common/services/specification.py`), and updates the user's skill graph.
- **Cognitive Technique:** **Feedback Loops**, **Elaboration** - Provides immediate, specific feedback based on official EGÉ criteria (KES/KOS) and suggests related concepts.
- **Component:** `api/endpoints/answer.py`, `api/services/answer_service.py`, `utils/answer_checker.py`, `utils/database_manager.py`, `utils/local_storage.py`, `utils/skill_graph.py`, `common/services/specification.py`, `common/models/problem_schema.py`.

### 5. Tracking Progress & Next Steps
- **User Action:** User views their progress dashboard or receives a recommendation.
- **System Response:** Displays progress based on the `InMemorySkillGraph` and suggests next steps (e.g., "Focus on Topic X", "Try a harder problem").
- **Cognitive Technique:** **Metacognition**, **Self-Explanation** - Helps user understand their strengths and weaknesses and encourages reflection on their learning process.
- **Component:** Frontend (React/Vue), `api/services/answer_service.py`, `utils/skill_graph.py`, `common/services/specification.py`.

## System Architecture Context
- The **Web API Service** handles the user-facing API endpoints (`api/`) and uses the `QuizServiceAdapter` and `AnswerService`.
- The **Scraping & Checking Service** handles data ingestion (`scraper/`) and answer validation (`utils/answer_checker.py`, `utils/browser_manager.py`), potentially called by the API service or running independently.
- The **Indexing Service** handles vector search setup (`utils/vector_indexer.py`), potentially called by the API service or running independently.
- The **Common Library** (`common/`) provides shared models (`common/models/`), services (`common/services/specification.py`), and utilities (`common/utils/`) used across all services.

