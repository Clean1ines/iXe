"""
Модуль FastAPI для обработки проверки ответов пользователей и сохранения состояния.
"""
from typing import Dict, Any, Optional
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

# NEW: Import DatabaseManager and FIPIAnswerChecker
from utils.database_manager import DatabaseManager
from utils.answer_checker import FIPIAnswerChecker

logger = logging.getLogger(__name__)

def create_app(db_manager: DatabaseManager, checker: FIPIAnswerChecker) -> FastAPI:
    """
    Factory function to create the FastAPI application instance.
    This allows dependency injection of db_manager and checker.
    """
    app = FastAPI(title="FIPI Answer API")

    # NEW: Store injected dependencies
    app.state.db_manager = db_manager
    app.state.checker = checker

    @app.get("/get_initial_state_for_page/{page_name}", response_class=HTMLResponse)
    async def get_initial_state_for_page(page_name: str) -> Dict[str, Any]:
        """
        Endpoint to get the initial state for all tasks on a given page.
        Returns a dictionary mapping task_id to its answer and status.
        NEW: Uses db_manager to fetch answers for the default user.
        """
        logger.info(f"API: Request for initial state for page: {page_name}")
        db_manager = app.state.db_manager # NEW: Retrieve from app state
        # NEW: Fetch all answers for the default user
        # This method returns {problem_id: {"answer": ..., "status": ...}}
        try:
            # ИСПРАВЛЕНО: Вызов метода с правильными аргументами
            all_user_answers = db_manager.get_answers_for_user_on_page(user_id="default_user", page_name=page_name)
            logger.debug(f"Fetched {len(all_user_answers)} answers from DB for user 'default_user' for page '{page_name}'.")
            # The get_answers_for_user_on_page method currently returns *all* answers for the user.
            # Filtering by page_name must happen in the DatabaseManager method itself
            # or the caller (e.g., in main.py when rendering) must provide context.
            # For now, we return the fetched answers.
            # In a more complex scenario, DBProblem would have a 'page_name' field,
            # and get_answers_for_user_on_page would join with it or use a prefix.
            # For this example, we assume the caller (like HTMLRenderer.render)
            # knows the task_ids for the page and will use this dictionary accordingly.
            # The current implementation of get_answers_for_user_on_page
            # returns all answers for the user. This is a simplification.
            # To truly filter by page, the DBManager needs a method like:
            # get_problem_ids_for_page(page_name, proj_id) -> List[problem_id]
            # and then get_answers_for_user_for_task_ids(user_id, task_ids)
            # For now, we return all user answers.
            # The frontend (INITIAL_PAGE_STATE) will only use the keys it needs.
            # This is not ideal for performance if there are many tasks.
            logger.info(f"API: Returning state for {len(all_user_answers)} tasks found for user 'default_user' for page '{page_name}'.")
            return all_user_answers
        except Exception as e:
            logger.error(f"Error loading initial state for page {page_name}: {e}", exc_info=True)
            # Return an empty dict as a fallback, or raise an HTTP error
            # depending on desired client-side behavior.
            # Returning an empty dict allows the frontend to proceed,
            # assuming no previous answers exist.
            return {}

    @app.post("/submit_answer")
    async def submit_answer(request: Request) -> Dict[str, Any]:
        """
        Endpoint to submit an answer and check it using FIPIAnswerChecker.
        Saves the result to the database.
        Returns the status, a descriptive message, and the raw response from the checker if applicable.
        """
        try:
            payload = await request.json()
            task_id = payload.get("task_id")
            answer = payload.get("answer")
            form_id = payload.get("form_id", "") # Default to empty string if not provided

            if not task_id or answer is None:
                raise HTTPException(status_code=422, detail="task_id and answer are required")

            logger.info(f"Received answer submission for task {task_id}, user answer length: {len(answer)}")
            db_manager = app.state.db_manager # NEW: Retrieve from app state
            checker = app.state.checker       # NEW: Retrieve from app state

            # Check if the answer already exists in the database
            existing_answer, existing_status = db_manager.get_answer_and_status(task_id)
            if existing_answer is not None:
                # If an answer exists, return the stored status without re-checking
                logger.info(f"Retrieved cached result for task {task_id}, status: {existing_status}")
                return {
                    "status": existing_status,
                    "message": f"Retrieved cached result: {existing_status}",
                    "answer": existing_answer # Include the cached answer
                }
            else:
                # If no answer exists, check the new answer
                check_result = await checker.check_answer(task_id, form_id, answer)
                status = check_result["status"]
                message = check_result["message"]

                # Save the answer and its status to the database
                db_manager.save_answer(task_id, answer, status)
                logger.info(f"Checked and saved new answer for task {task_id}, status: {status}")

                # Return the check result
                return check_result

        except Exception as e:
            logger.error(f"Error processing answer submission for task {task_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.post("/save_answer_only")
    async def save_answer_only(request: Request) -> Dict[str, str]:
        """
        Endpoint to save an answer without checking it.
        Useful for saving drafts or answers that will be checked later.
        """
        try:
            payload = await request.json()
            task_id = payload.get("task_id")
            answer = payload.get("answer")

            if not task_id or answer is None:
                raise HTTPException(status_code=422, detail="task_id and answer are required")

            logger.info(f"Received request to save answer only for task {task_id}, answer length: {len(answer)}")
            db_manager = app.state.db_manager # NEW: Retrieve from app state

            # Save the answer with the status "not_checked"
            db_manager.save_answer(task_id, answer, "not_checked")
            logger.info(f"Saved answer for task {task_id} with status 'not_checked'")

            return {"message": f"Answer for task {task_id} saved successfully with status 'not_checked'."}

        except Exception as e:
            logger.error(f"Error saving answer for task {task_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return app

