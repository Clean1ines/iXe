# api/endpoints/subjects.py
from fastapi import APIRouter, Depends, HTTPException
import logging
from utils.database_manager import DatabaseManager
from api.dependencies import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/subjects/available")
async def get_available_subjects(db: DatabaseManager = Depends(get_db_manager)):
    """
    API endpoint to get a list of available subjects.

    This endpoint fetches the list of subjects from the database
    based on the available problems.
    """
    try:
        all_problems = db.get_all_problems()
        subjects = list({p.subject for p in all_problems})
        logger.info(f"Available subjects: {subjects}")
        return {"subjects": subjects}
    except Exception as e:
        logger.error(f"Error fetching subjects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
