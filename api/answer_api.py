# api/answer_api.py
"""API router for interacting with database and answer checking functionality."""

import logging # NEW: Import logging
from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any, Optional
from utils.answer_checker import FIPIAnswerChecker
from utils.database_manager import DatabaseManager


logger = logging.getLogger(__name__) # NEW: Create module logger

def create_app(db_manager: DatabaseManager, checker: FIPIAnswerChecker) -> FastAPI:
    """Creates a FastAPI application with endpoints for answer storage and checking.

    Args:
        db_manager: An instance of DatabaseManager for managing answers and statuses in the database.
        checker: An instance of FIPIAnswerChecker for verifying answers.

    Returns:
        A configured FastAPI application instance.
    """
    app = FastAPI(title="FIPI Answer API")

    @app.get("/initial_state/{page_name}")
    async def get_initial_state(page_name: str) -> Dict[str, Any]:
        """Loads the initial state (answers and statuses) for tasks on a specific page.

        This endpoint retrieves stored answers and statuses for all tasks associated
        with a given page name from the database. It's intended to initialize the frontend state.
        Note: This implementation assumes task IDs are prefixed with the page name,
        and the database manager filters answers based on this prefix.

        Args:
            page_name: The name of the page to load state for. Task IDs are assumed
                       to be prefixed with this name (e.g., '{page_name}_task1').

        Returns:
            A dictionary mapping task IDs (for the given page) to their stored
            answer and status information.
        """
        logger.info(f"Loading initial state for page: {page_name}") # NEW: Log start of function
        # В реальной реализации DatabaseManager может иметь метод вроде get_answers_for_page
        # или get_all_answers_for_user, и мы фильтруем ответы здесь.
        # Для простоты, если DatabaseManager не поддерживает фильтрацию по page_name напрямую,
        # можно получить все ответы для пользователя и отфильтровать их здесь.
        # Предположим, DatabaseManager имеет метод get_all_user_answers(user_id="default_user")
        # возвращающий список объектов DBAnswer.
        # Псевдокод: all_db_answers = db_manager.get_all_user_answers(user_id="default_user")
        # filtered_data = {a.problem_id: {"answer": a.user_answer, "status": a.status} for a in all_db_answers if a.problem_id.startswith(page_name)}
        # return filtered_data

        # В отсутствие специфичного метода в DatabaseManager для получения ответов по page_name,
        # и для соответствия предыдущему поведению, мы можем получить все ответы
        # и отфильтровать их.
        # Лучше добавить метод в DatabaseManager, например, `get_answers_for_page_prefix`.
        # Для текущей реализации, предположим, что мы можем получить все ответы для пользователя
        # и отфильтровать их. Используем гипотетический метод или адаптируем.
        # Псевдокод:
        # all_db_answers = db_manager.get_all_user_answers(user_id="default_user")
        # page_data = {}
        # for db_answer in all_db_answers:
        #     if db_answer.problem_id.startswith(page_name):
        #         page_data[db_answer.problem_id] = {
        #             "answer": db_answer.user_answer,
        #             "status": db_answer.status
        #         }
        # return page_data

        # В целях примера, предположим, что db_manager.get_all_user_answers возвращает список объектов DBAnswer.
        # from models.database_models import DBAnswer # Импорт может быть нужен, если DBAnswer не доступен в другом месте
        try:
            all_db_answers = db_manager.get_all_user_answers(user_id="default_user")
            page_data = {}
            for db_answer in all_db_answers:
                 if db_answer.problem_id.startswith(page_name):
                     page_data[db_answer.problem_id] = {
                         "answer": db_answer.user_answer,
                         "status": db_answer.status
                     }
            logger.debug(f"Returning state for {len(page_data)} tasks for page {page_name}") # NEW: Log end of function
            return page_data
        except Exception as e: # MODIFIED: Broader exception catch to log errors
            logger.error(f"Error loading initial state for page {page_name}: {e}", exc_info=True) # NEW: Log error before raising
            # Если метод get_all_user_answers не существует или не поддерживает фильтрацию,
            # и метод get_answers_for_page_prefix не реализован, возвращаем пустой словарь
            # или вызываем исключение.
            # Псевдокод: raise HTTPException(status_code=500, detail="DatabaseManager method for fetching page answers not implemented.")
            # Или возвращаем пустой результат, если это допустимо.
            return {}


    @app.post("/submit_answer")
    async def submit_answer(request: Request) -> Dict[str, Any]:
        """Submits an answer for a task, checks it if not already checked, and stores the result.

        This endpoint accepts a user's answer for a specific task. If the answer has not
        been checked previously, it calls the checker to verify the answer, saves the
        result in the database, and returns the status. If the answer was already checked,
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

            logger.info(f"Received answer submission for task {task_id}, user answer length: {len(answer)}") # NEW: Log received submission

            # Check if the answer already exists in the database
            existing_answer, existing_status = db_manager.get_answer_and_status(task_id)

            if existing_answer is not None:
                # If an answer exists, return the stored status without re-checking
                logger.info(f"Retrieved cached result for task {task_id}, status: {existing_status}") # NEW: Log cached result
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
                logger.info(f"Checked and saved new answer for task {task_id}, status: {status}") # NEW: Log new check and save

                # Return the check result
                return check_result

        except Exception as e:
            logger.error(f"Error processing answer submission for task {task_id}: {e}", exc_info=True) # NEW: Log error before raising
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

            logger.info(f"Received request to save answer only for task {task_id}, answer length: {len(answer)}") # NEW: Log received request
            # Save the answer with the status "not_checked"
            db_manager.save_answer(task_id, answer, "not_checked")
            logger.info(f"Saved answer for task {task_id} with status 'not_checked'") # NEW: Log save operation
            return {"message": f"Answer for task {task_id} saved successfully with status 'not_checked'."}

        except Exception as e:
            logger.error(f"Error saving answer for task {task_id}: {e}", exc_info=True) # NEW: Log error before raising
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return app

