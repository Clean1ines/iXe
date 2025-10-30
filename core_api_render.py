"""
FastAPI application for Render.com deployment.
Stateless, read-only version of the core API.
All user progress is managed by the Telegram Mini App frontend via localStorage.
Supports fully offline-ready HTML via Problem.offline_html.
"""
from typing import Any, Dict, List
import logging
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from utils.database_manager import DatabaseManager
from utils.answer_checker import FIPIAnswerChecker
from config import FIPI_QUESTIONS_URL

logger = logging.getLogger(__name__)

# Use relative path for local dev; works in Docker if data/ is copied to /app/data/
DB_PATH = str(Path(__file__).parent / "data" / "fipi_data.db")

# Initialize dependencies
db_manager = DatabaseManager(DB_PATH)
checker = FIPIAnswerChecker(base_url=FIPI_QUESTIONS_URL)

problem_count = len(db_manager.get_all_problems())
logger.info(f"✅ Render API started. Loaded {problem_count} problems from {DB_PATH}")

app = FastAPI(
    title="FIPI Core API (Render)",
    description="Stateless, read-only API for Telegram Mini App.",
    version="1.0.1"
)

# Mount PWA
FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    logger.info(f"Mounting PWA from: {FRONTEND_DIR}")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="pwa")
else:
    logger.warning("Frontend build not found. Skipping PWA mount.")

@app.get("/health")
async def root() -> Dict[str, Any]:
    return {"message": "FIPI Core API is running", "problems_loaded": problem_count}

@app.post("/quiz/daily/start")
async def start_daily_quiz(request: Request) -> Dict[str, Any]:
    try:
        all_problems = db_manager.get_all_problems()
        problems = all_problems[:10]
        quiz_id = f"daily_quiz_{uuid.uuid4().hex[:8]}"
        items = []
        for problem in problems:
            topic = problem.topics[0] if problem.topics else "general"
            prompt = problem.offline_html or problem.text
            items.append({
                "problem_id": problem.problem_id,
                "subject": problem.subject,
                "topic": topic,
                "prompt": prompt,
                "choices_or_input_type": "text_input"
            })
        logger.info(f"Generated quiz '{quiz_id}' with {len(items)} items")
        return {"quiz_id": quiz_id, "items": items}
    except Exception as e:
        logger.error(f"Error in /quiz/daily/start: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/answer")
async def check_answer(request: Request) -> Dict[str, Any]:
    try:
        data = await request.json()
        problem_id = data.get("problem_id")
        user_answer = data.get("user_answer")
        form_id = data.get("form_id")

        if not problem_id or user_answer is None or not form_id:
            raise HTTPException(status_code=422, detail="problem_id, user_answer, and form_id are required")

        logger.info(f"Checking answer for problem '{problem_id}'")
        result = await checker.check_answer(problem_id, form_id, user_answer)
        verdict = result["status"]
        score_float = 1.0 if verdict == "correct" else (0.0 if verdict == "incorrect" else -1.0)

        return {
            "verdict": verdict,
            "score_float": score_float,
            "short_hint": result["message"],
            "evidence": [],
            "deep_explanation_id": None
        }

    except Exception as e:
        logger.error(f"Error in /answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/plan/generate")
async def generate_study_plan(request: Request) -> Dict[str, Any]:
    return {"plan_id": f"plan_{uuid.uuid4().hex[:8]}", "weeks": []}
