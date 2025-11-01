from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from utils.database_manager import DatabaseManager
from processors.html_renderer import HTMLRenderer
from api.dependencies import get_db_manager

router = APIRouter(tags=["blocks"])

def get_html_renderer(db: DatabaseManager = Depends(get_db_manager)) -> HTMLRenderer:
    """
    Dependency to provide an instance of HTMLRenderer.
    """
    return HTMLRenderer(db_manager=db)

@router.get("/block/{problem_id}", response_class=HTMLResponse)
async def get_block_html(
    problem_id: str,
    renderer: HTMLRenderer = Depends(get_html_renderer)
):
    """
    Returns an HTML block for a given problem, rendered on the fly from the Problem model.
    Uses ONLY problem.text — the offline_html field is no longer supported.
    """
    problem = renderer._db_manager.get_problem_by_id(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    block_index = abs(hash(problem_id)) % (10 ** 8)

    try:
        html = renderer.render_block_from_problem(problem=problem, block_index=block_index)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")
