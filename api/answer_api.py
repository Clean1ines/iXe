# api/answer_api.py
"""API router for interacting with local storage and answer checking functionality."""

from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any, Optional
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker


def create_app(storage: LocalStorage, checker: FIPIAnswerChecker) -> FastAPI:
    """Creates a FastAPI application with endpoints for answer storage and checking.

    Args:
        storage: An instance of LocalStorage for managing answers and statuses.
        checker: An instance of FIPIAnswerChecker for verifying answers.

    Returns:
        A configured FastAPI application instance.
    """
    app = FastAPI(title="FIPI Answer API")

    @app.get("/initial_state/{page_name}")
    async def get_initial_state(page_name: str) -> Dict[str, Any]:
        """Loads the initial state (answers and statuses) for tasks on a specific page.

        This endpoint retrieves stored answers and statuses for all tasks associated
        with a given page name. It's intended to initialize the frontend state.

        Args:
            page_name: The name of the page to load state for. Task IDs are assumed
                       to be prefixed with this name (e.g., '{page_name}_task1').

        Returns:
            A dictionary mapping task IDs (for the given page) to their stored
            answer and status information.
        """
        # For simplicity, this implementation assumes task IDs are globally unique
        # or that the storage implementation can filter by a prefix like page_name.
        # A more robust approach might involve storing page-to-task mappings separately
        # or having LocalStorage support prefix-based retrieval.
        all_data = storage._load_data() # Accessing private method for full data dump
        page_data = {k: v for k, v in all_data.items() if k.startswith(page_name)}
        return page_data

    @app.post("/submit_answer")
    async def submit_answer(request: Request) -> Dict[str, Any]:
        """Submits an answer for a task, checks it if not already checked, and stores the result.

        This endpoint accepts a user's answer for a specific task. If the answer has not
        been checked previously, it calls the checker to verify the answer, saves the
        result in storage, and returns the status. If the answer was already checked,
        it returns the stored status without re-checking.

        Args:
            request: The incoming request object containing JSON data with
                     'task_id', 'answer', and optionally 'form_id'.

        Returns:
            A dictionary containing the status ('correct', 'incorrect', 'error'),
            a descriptive message, and the raw response from the checker if applicable.
        """
        try:
            payload = await request.json()
            task_id = payload.get("task_id")
            answer = payload.get("answer")
            form_id = payload.get("form_id", "") # Default to empty string if not provided

            if not task_id or answer is None:
                 raise HTTPException(status_code=422, detail="task_id and answer are required")

            # Check if the answer already exists in storage
            existing_answer, existing_status = storage.get_answer_and_status(task_id)

            if existing_answer is not None:
                # If an answer exists, return the stored status without re-checking
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

                # Save the answer and its status to storage
                storage.save_answer_and_status(task_id, answer, status)

                # Return the check result
                return check_result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.post("/save_answer_only")
    async def save_answer_only(request: Request) -> Dict[str, str]:
        """Saves an answer for a task without checking it, setting its status to 'not_checked'.

        This endpoint is useful for saving user input locally without immediately
        triggering an external check, for example, for draft answers or offline storage.

        Args:
            request: The incoming request object containing JSON data with
                     'task_id' and 'answer'.

        Returns:
            A dictionary confirming the save operation.
        """
        try:
            payload = await request.json()
            task_id = payload.get("task_id")
            answer = payload.get("answer")

            if not task_id or answer is None:
                 raise HTTPException(status_code=422, detail="task_id and answer are required")

            # Save the answer with the status "not_checked"
            storage.save_answer_and_status(task_id, answer, "not_checked")
            return {"message": f"Answer for task {task_id} saved successfully with status 'not_checked'."}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return app
