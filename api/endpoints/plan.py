from fastapi import APIRouter, Request, HTTPException
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/plan/generate")
async def generate_study_plan(request: Request):
    return {
        "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
        "weeks": []
    }
