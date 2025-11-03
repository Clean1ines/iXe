from fastapi import APIRouter, Depends, HTTPException
from utils.database_manager import DatabaseManager
from api.dependencies import get_db_manager
from api.schemas import GetBlockResponse, ProblemResponse

router = APIRouter(tags=["blocks"])

@router.get("/problem/{problem_id}", response_model=GetBlockResponse)
async def get_problem_data(
    problem_id: str,
    db: DatabaseManager = Depends(get_db_manager)
):
    """
    Returns problem data for frontend rendering.
    """
    problem = db.get_problem_by_id(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    block_index = abs(hash(problem_id)) % (10 ** 8)

    try:
        problem_response = ProblemResponse.from_problem_model(problem, block_index=block_index)
        response = GetBlockResponse(problem=problem_response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve problem data: {str(e)}")
