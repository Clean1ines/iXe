"""
Модуль FastAPI для основных эндпоинтов MVP приложения подготовки к ЕГЭ.
Содержит заглушки для квизов, проверки ответов и генерации плана.
"""
from typing import Dict, List, Any, Optional
import logging
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse # NEW: Import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware # NEW: Import CORSMiddleware

from utils.database_manager import DatabaseManager
from models.problem_schema import Problem
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from scraper import fipi_scraper # NEW: Import scraper for subject listing
import config # NEW: Import config for subject listing
from processors.html_renderer import HTMLRenderer # NEW: Import HTMLRenderer
from utils.task_id_utils import extract_task_id_and_form_id # NEW: Import utils

logger = logging.getLogger(__name__)

# NEW: Global variable placeholder for scraping status (in a real app, use a proper store)
scraping_status_global = {"is_running": False, "current_subject": None, "progress": 0}

def create_core_app(db_manager: DatabaseManager, storage: LocalStorage, checker: FIPIAnswerChecker, scraping_status: Optional[Dict] = None) -> FastAPI:
    """
    Factory function to create the core FastAPI application instance.

    This app provides MVP endpoints for quizzes, answer checking, and study planning.
    It uses dependency injection to access the DatabaseManager, LocalStorage, and FIPIAnswerChecker.

    Args:
        db_manager (DatabaseManager): An instance of DatabaseManager for data access.
        storage (LocalStorage): An instance of LocalStorage for caching answers.
        checker (FIPIAnswerChecker): An instance of FIPIAnswerChecker for validating answers.
        scraping_status (Optional[Dict]): Global scraping status dictionary.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    global scraping_status_global
    if scraping_status is not None:
        scraping_status_global = scraping_status

    app = FastAPI(
        title="FIPI Core API (MVP)",
        description="API for quiz generation, answer checking, and study planning. MVP implementation.",
        version="0.1.0"
    )

    # NEW: Add CORS middleware to allow requests from the frontend domain
    app.add_middleware(
        CORSMiddleware,
        # Укажи оба источника
        allow_origins=["https://ixem.duckdns.org", "http://localhost:3000", "http://localhost:5173"], # Добавь нужные
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store the injected dependencies
    app.state.db_manager = db_manager
    app.state.storage = storage
    app.state.checker = checker

    @app.get("/")
    async def root() -> Dict[str, str]:
        """
        Health check endpoint for the core API.

        Returns:
            Dict[str, str]: A simple message indicating the API is running.
        """
        return {"message": "FIPI Core API (MVP) is running"}

    @app.get("/subjects/available") # NEW: Endpoint to list available subjects
    async def get_available_subjects() -> Dict[str, List[str]]:
        """
        Returns a list of subjects for which data is available.

        Returns:
            Dict[str, List[str]]: A dictionary containing a list of subject names.
        """
        try:
            # NEW: Fetch subjects from the database or based on available run folders
            # For now, return a placeholder list. In a real implementation,
            # this could query a subjects table or list folders.
            # Let's simulate reading from the database schema or a config if subjects are stored there.
            # For this MVP, we'll hardcode based on the loaded data's subject field.
            # Let's get unique subjects from the loaded problems.
            all_problems = db_manager.get_all_problems()
            subjects_set = set()
            for problem in all_problems:
                subjects_set.add(problem.subject)
            unique_subjects = list(subjects_set)
            logger.info(f"Available subjects from DB: {unique_subjects}")
            return {"subjects": unique_subjects}
        except Exception as e:
            logger.error(f"Error fetching available subjects: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error while fetching subjects")

    # NEW: Endpoint to render a single block from problem_id
    @app.get("/api/v1/block/{problem_id}", response_class=HTMLResponse)
    async def get_block_html(request: Request, problem_id: str) -> str:
        """
        Generates and returns the HTML for a single task block based on the problem_id.

        Args:
            request (Request): The incoming request object.
            problem_id (str): The unique identifier of the problem in the database.

        Returns:
            str: The complete HTML string for the single block.
        """
        logger.info(f"Requesting HTML block for problem_id: {problem_id}")
        try:
            # 2. Get db_manager from app.state
            db_manager_instance: DatabaseManager = request.app.state.db_manager

            # 3. Fetch problem by ID
            problem = db_manager_instance.get_problem_by_id(problem_id)
            if not problem:
                logger.warning(f"Problem with ID {problem_id} not found in database.")
                # 4. Raise HTTPException if not found
                raise HTTPException(status_code=404, detail=f"Problem with ID {problem_id} not found.")

            # 5. Initialize HTMLRenderer
            # The renderer needs db_manager for initial state, which we have from app.state
            html_renderer = HTMLRenderer(db_manager_instance)

            # 6. Call new method render_block_from_problem
            # Using a default block_index of 0 for single block requests
            block_index = 0
            generated_html = html_renderer.render_block_from_problem(problem, block_index)

            logger.info(f"Successfully generated HTML block for problem_id: {problem_id}")
            # 7. Return generated HTML
            return generated_html

        except HTTPException:
            # Re-raise HTTP exceptions (like 404)
            raise
        except Exception as e:
            logger.error(f"Error generating HTML block for problem_id {problem_id}: {e}", exc_info=True)
            logger.exception("Full traceback for block generation error:") # Log full traceback
            raise HTTPException(status_code=500, detail="Internal server error while generating block HTML")


    @app.post("/quiz/daily/start")
    async def start_daily_quiz(request: Request) -> Dict[str, Any]:
        """
        Starts a new daily quiz by fetching a set of problems from the database.

        Args:
            request (Request): The incoming request object containing JSON payload.
                Expected payload: {"page_name": "optional_page_name"}

        Returns:
            Dict[str, Any]: A dictionary containing the quiz ID and a list of quiz items.
                Format: {"quiz_id": "...", "items": [{"problem_id": "...", "subject": "...", "topic": "...", "prompt": "...", "choices_or_input_type": "...", "form_id": "..."}]}
        """
        try:
            payload = await request.json()
            # NEW: Use page_name for filtering, default to 'init' if not provided
            page_name = payload.get("page_name", "init")
            logger.info(f"Starting daily quiz for page: {page_name}")

            db_manager: DatabaseManager = app.state.db_manager
            # NEW: Filter problems by subject/page_name if possible.
            # For now, let's assume page_name maps to a subject or tag.
            # Since Problem model has subject, we can filter by it.
            # Let's map page_name to a subject tag if needed.
            # For simplicity in this stub, we'll fetch all problems and take first 10.
            # A real implementation would use db_manager.get_problems_by_subject_or_page(page_name)
            all_problems = db_manager.get_all_problems()
            # NEW: Filter by subject if page_name corresponds to a subject
            filtered_problems = [p for p in all_problems if p.subject == page_name or p.problem_id.startswith(f"{page_name}_")]
            if not filtered_problems:
                 logger.warning(f"No problems found for page_name/subject '{page_name}', fetching all.")
                 filtered_problems = all_problems

            # For MVP, let's take a smaller sample, e.g., first 10
            problems = filtered_problems[:10]

            quiz_id = f"daily_quiz_{uuid.uuid4().hex[:8]}"
            items = []
            for problem in problems:
                # Extract fields
                problem_id = problem.problem_id
                subject = problem.subject
                # Assuming topics is a list, take the first one or join them
                topic = problem.topics[0] if problem.topics else "general"
                # Truncate prompt for brevity (maybe don't truncate for real use)
                prompt = problem.text # Keep full text for now
                # NEW: Add form_id. Since we don't have it directly from DB, derive from problem_id or use a default.
                # In the original HTML rendering, form_id was generated. We need a consistent way to generate or store it.
                # For now, let's create a default form_id based on problem_id.
                form_id = f"form_{problem_id}"
                # Default to text input for all problems in this stub
                choices_or_input_type = "text_input"

                item = {
                    "problem_id": problem_id,
                    "subject": subject,
                    "topic": topic,
                    "prompt": prompt,
                    "choices_or_input_type": choices_or_input_type,
                    "form_id": form_id # NEW: Add form_id
                }
                items.append(item)

            logger.info(f"Generated quiz '{quiz_id}' with {len(items)} items for page '{page_name}'.")

            return {
                "quiz_id": quiz_id,
                "items": items
            }
        except Exception as e:
            logger.error(f"Error starting daily quiz: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error while starting quiz")

    @app.post("/quiz/{quiz_id}/finish")
    async def finish_quiz(quiz_id: str, request: Request) -> Dict[str, Any]:
        """
        Processes the results of a completed quiz.

        Args:
            quiz_id (str): The unique identifier of the quiz being finished.
            request (Request): The incoming request object containing JSON payload.
                Expected payload: {"results": [{"problem_id": "...", "user_answer": "...", "time_spent": ...}]}

        Returns:
            Dict[str, Any]: A dictionary containing the quiz score, accuracy by topic, and recommendations.
                Format: {"score": 0.0, "per_topic_accuracy": {}, "recommended_actions": []}
        """
        try:
            payload = await request.json()
            results = payload.get("results", [])
            logger.info(f"Finishing quiz '{quiz_id}' with {len(results)} results received.")

            # Log the received results for debugging
            logger.debug(f"Results for quiz {quiz_id}: {results}")

            # Placeholder logic for calculating score and accuracy
            # In a real implementation, this would check answers against the database.
            total = len(results)
            correct = 0  # Placeholder, no actual checking in stub
            score = round(correct / total if total > 0 else 0, 2) if total > 0 else 0.0

            # Placeholder for per-topic accuracy
            per_topic_accuracy: Dict[str, float] = {}  # Placeholder
            # Placeholder for recommendations
            recommended_actions: List[str] = ["Повторите тему 'Алгебраические выражения'"]  # Placeholder

            response = {
                "score": score,
                "per_topic_accuracy": per_topic_accuracy,
                "recommended_actions": recommended_actions
            }

            logger.info(f"Quiz '{quiz_id}' finished. Calculated score: {score}.")
            return response

        except Exception as e:
            logger.error(f"Error finishing quiz '{quiz_id}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error while finishing quiz")

    @app.post("/answer")
    async def check_answer(request: Request) -> Dict[str, Any]:
        """
        Checks a single user answer against the correct one using FIPIAnswerChecker.
        Caches the result using LocalStorage.

        Args:
            request (Request): The incoming request object containing JSON payload.
                Expected payload: {"problem_id": "...", "user_answer": "...", "form_id": "..."}

        Returns:
            Dict[str, Any]: A dictionary containing the verdict, score, hint, evidence, and explanation ID.
                Format: {"verdict": "correct|incorrect|error", "score_float": 0.0, "short_hint": "...", "evidence": [], "deep_explanation_id": null}
        """
        try:
            request_data = await request.json()
            problem_id = request_data.get("problem_id")
            user_answer = request_data.get("user_answer")
            form_id = request_data.get("form_id") # Required for FIPI checker

            if not problem_id or user_answer is None or not form_id:
                raise HTTPException(status_code=422, detail="problem_id, user_answer, and form_id are required")

            logger.info(f"Checking answer for problem '{problem_id}'. User answer length: {len(user_answer)}")

            # Retrieve dependencies from app state
            storage: LocalStorage = request.app.state.storage
            checker: FIPIAnswerChecker = request.app.state.checker

            # Check if the answer is already cached
            stored_answer, stored_status = storage.get_answer_and_status(problem_id)
            if stored_answer is not None and stored_status in ["correct", "incorrect"]:
                logger.info(f"Answer for {problem_id} found in cache: {stored_status}")
                return {
                    "verdict": stored_status,
                    "score_float": 1.0 if stored_status == "correct" else 0.0,
                    "short_hint": "Ответ загружен из кэша.",
                    "evidence": [],
                    "deep_explanation_id": None
                }

            # If not cached or status is 'not_checked', perform the check
            check_result = await checker.check_answer(problem_id, form_id, user_answer)
            status = check_result["status"]
            message = check_result["message"]

            # Save the result to storage
            storage.save_answer_and_status(problem_id, user_answer, status)

            # Prepare the response based on the check result
            score_float = 1.0 if status == "correct" else (0.0 if status == "incorrect" else -1.0)

            response = {
                "verdict": status,
                "score_float": score_float,
                "short_hint": message,
                "evidence": [],
                "deep_explanation_id": None
            }

            logger.info(f"Answer for problem '{problem_id}' checked. Verdict: {status}.")
            return response

        except HTTPException:
            # Re-raise HTTP exceptions (like 422)
            raise
        except Exception as e:
            logger.error(f"Error checking answer for problem '{problem_id}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error while checking answer")

    @app.post("/plan/generate")
    async def generate_study_plan(request: Request) -> Dict[str, Any]:
        """
        Generates a personalized study plan based on user preferences.

        Args:
            request (Request): The incoming request object containing JSON payload.
                Expected payload: {"user_id": "...", "target_date": "...", "time_per_week_hours": ...}

        Returns:
            Dict[str, Any]: A dictionary containing the plan ID and a list of weekly plans.
                Format: {"plan_id": "...", "weeks": [{"week_number": 1, "focus_topics": ["..."], "daily_tasks": ["..."]}]}}
        """
        try:
            payload = await request.json()
            user_id = payload.get("user_id")
            target_date = payload.get("target_date")
            time_per_week_hours = payload.get("time_per_week_hours")

            if not user_id or target_date is None or time_per_week_hours is None:
                raise HTTPException(status_code=422, detail="user_id, target_date, and time_per_week_hours are required")

            logger.info(f"Generating study plan for user '{user_id}', target date: {target_date}, hours per week: {time_per_week_hours}")

            # Placeholder logic for plan generation
            # In a real implementation, this would use user history, difficulty, and target date.
            plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            weeks = [
                {
                    "week_number": 1,
                    "focus_topics": ["Алгебраические выражения", "Уравнения"],
                    "daily_tasks": ["Задание 1", "Задание 2", "Задание 3"]
                },
                {
                    "week_number": 2,
                    "focus_topics": ["Геометрия", "Функции"],
                    "daily_tasks": ["Задание 1", "Задание 2", "Задание 3"]
                }
            ]

            response = {
                "plan_id": plan_id,
                "weeks": weeks
            }

            logger.info(f"Study plan '{plan_id}' generated for user '{user_id}'.")
            return response

        except Exception as e:
            logger.error(f"Error generating study plan for user '{user_id}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error while generating study plan")

    return app

# Для запуска через uvicorn, если нужно запустить этот файл напрямую с фиктивными зависимостями
# if __name__ == "__main__":
#     import uvicorn
#     # Заглушка для зависимостей
#     fake_db = DatabaseManager(":memory:") # In-memory DB for example
#     fake_storage = LocalStorage(":memory:")
#     fake_checker = FIPIAnswerChecker(base_url="http://example.com")
#     app_instance = create_core_app(fake_db, fake_storage, fake_checker)
#     uvicorn.run(app_instance, host="0.0.0.0", port=8000)
