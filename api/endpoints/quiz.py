from fastapi import APIRouter, Request, Depends, HTTPException
import uuid
import logging
from utils.database_manager import DatabaseManager
from api.dependencies import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/quiz/daily/start")
async def start_daily_quiz(
    request: Request,
    db: DatabaseManager = Depends(get_db_manager)
):
    try:
        payload = await request.json()
        page_name = payload.get("page_name", "init")
        logger.info(f"Starting quiz for page: {page_name}")

        all_problems = db.get_all_problems()
        filtered = [p for p in all_problems if p.subject == page_name or p.problem_id.startswith(f"{page_name}_")]
        problems = (filtered or all_problems)[:10]

        items = []
        for p in problems:
            prompt = p.offline_html or p.text
            items.append({
                "problem_id": p.problem_id,
                "subject": p.subject,
                "topic": p.topics[0] if p.topics else "general",
                "prompt": prompt,
                "choices_or_input_type": "text_input"
            })

        quiz_id = f"daily_quiz_{uuid.uuid4().hex[:8]}"
        return {"quiz_id": quiz_id, "items": items}

    except Exception as e:
        logger.error(f"Quiz start error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
