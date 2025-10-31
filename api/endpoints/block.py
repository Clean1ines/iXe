from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from utils.database_manager import DatabaseManager
from processors.html_renderer import HTMLRenderer
from api.dependencies import get_db_manager

router = APIRouter(prefix="/api/v1", tags=["blocks"])

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
    Возвращает HTML-блок задания, срендеренный на лету из модели Problem.
    Использует ТОЛЬКО problem.text — offline_html больше не поддерживается.
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
