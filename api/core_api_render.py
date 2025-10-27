"""
FastAPI application for Render.com deployment.
Stateless, read-only version of the core API.
All user progress is managed by the Telegram Mini App frontend via localStorage.
"""
from typing import Any, Dict, List
import logging
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from utils.database_manager import DatabaseManager
from utils.answer_checker import FIPIAnswerChecker
from config import FIPI_QUESTIONS_URL

logger = logging.getLogger(__name__)

# Read-only database path (embedded in Docker image)
DB_PATH = "/app/data/fipi_data.db"

# Initialize dependencies once at startup
db_manager = DatabaseManager(DB_PATH)
checker = FIPIAnswerChecker(base_url=FIPI_QUESTIONS_URL)

app = FastAPI(
    title="FIPI Core API (Render)",
    description="Stateless, read-only API for Telegram Mini App. All user data is stored in the client.",
    version="1.0.0"
)

@app.get("/")
async def root() -> Dict[str, str]:
    """
    Health check endpoint.
    Returns:
        Dict[str, str]: Simple confirmation that the service is running.
    """
    return {"message": "FIPI Core API (Render) is running"}

@app.post("/quiz/daily/start")
async def start_daily_quiz(request: Request) -> Dict[str, Any]:
    """
    Starts a new daily quiz by returning the first 10 problems from the embedded database.
    This endpoint does not use user context or filters — it's purely read-only.
    
    Args:
        request (Request): Incoming request. Payload may contain "page_name" (ignored).
    
    Returns:
        Dict[str, Any]: Quiz ID and list of quiz items with problem_id, subject, topic, prompt, and input type.
    """
    try:
        payload = await request.json()
        page_name = payload.get("page_name", "init")
        logger.info(f"Starting daily quiz (Render mode). Page: {page_name}")

        all_problems = db_manager.get_all_problems()
        problems = all_problems[:10]  # MVP: first 10 tasks

        quiz_id = f"daily_quiz_{uuid.uuid4().hex[:8]}"
        items = []
        for problem in problems:
            topic = problem.topics[0] if problem.topics else "general"
            prompt = problem.text[:200] + "..." if len(problem.text) > 200 else problem.text
            items.append({
                "problem_id": problem.problem_id,
                "subject": problem.subject,
                "topic": topic,
                "prompt": prompt,
                "choices_or_input_type": "text_input"
            })

        logger.info(f"Generated quiz '{quiz_id}' with {len(items)} items (Render mode).")
        return {"quiz_id": quiz_id, "items": items}

    except Exception as e:
        logger.error(f"Error in /quiz/daily/start (Render): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/answer")
async def check_answer(request: Request) -> Dict[str, Any]:
    """
    Validates a single user answer by forwarding it to the FIPI checker.
    Does NOT cache or store the result — frontend is responsible for persistence.
    
    Args:
        request (Request): Must contain "problem_id", "user_answer", "form_id".
    
    Returns:
        Dict[str, Any]: Verdict ("correct"/"incorrect"/"error"), score, hint, and metadata.
    """
    try:
        data = await request.json()
        problem_id = data.get("problem_id")
        user_answer = data.get("user_answer")
        form_id = data.get("form_id")

        if not problem_id or user_answer is None or not form_id:
            raise HTTPException(status_code=422, detail="problem_id, user_answer, and form_id are required")

        logger.info(f"Checking answer for problem '{problem_id}' (Render mode).")

        # Direct check — no caching
        result = await checker.check_answer(problem_id, form_id, user_answer)
        verdict = result["status"]
        score_float = 1.0 if verdict == "correct" else (0.0 if verdict == "incorrect" else -1.0)

        response = {
            "verdict": verdict,
            "score_float": score_float,
            "short_hint": result["message"],
            "evidence": [],
            "deep_explanation_id": None
        }

        logger.info(f"Answer checked for '{problem_id}': {verdict} (Render mode).")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /answer (Render): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Optional: stub for /plan/generate (not used in MVP)
@app.post("/plan/generate")
async def generate_study_plan(request: Request) -> Dict[str, Any]:
    """
    Stub for study plan generation (not implemented in Render mode).
    """
    return {
        "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
        "weeks": []
    }
