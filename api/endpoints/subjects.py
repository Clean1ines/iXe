from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import List
from utils.database_manager import DatabaseManager
from api.dependencies import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/subjects/available")
async def get_available_subjects(db: DatabaseManager = Depends(get_db_manager)):
    """
    API endpoint to get a list of available subjects.
    The list reflects subjects present in the database, typically determined by DISTINCT subject names from problem entries.
    """
    try:
        subjects = db.get_all_subjects()
        logger.info(f"Available subjects: {subjects}")
        return {"subjects": subjects}
    except Exception as e:
        logger.error(f"Error fetching subjects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")

@router.get("/subjects/{subject}/random_problems")
async def get_random_problems(
    subject: str,
    count: int = 10,
    db: DatabaseManager = Depends(get_db_manager)
):
    """
    Returns `count` random problem IDs for the given subject.
    """
    if count < 1 or count > 50:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 50")
    try:
        problem_ids = db.get_random_problem_ids(subject=subject, count=count)
        return {"problem_ids": problem_ids}
    except Exception as e:
        logger.error(f"Error fetching random problems for subject {subject}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
