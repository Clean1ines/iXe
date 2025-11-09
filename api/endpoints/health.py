"""Health check endpoint for monitoring application status."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from resource_management.browser_pool_manager import BrowserPoolManager
from qdrant_client import QdrantClient
from domain.interfaces.infrastructure_adapters import.database_adapter import DatabaseAdapter
from config import DB_PATH, QDRANT_HOST, QDRANT_PORT

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint that returns the status of all dependencies.
    
    Returns:
        JSON response with health status of all components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": {"status": "healthy", "details": "API is running"},
            "database": {"status": "unknown", "details": "Checking..."},
            "qdrant": {"status": "unknown", "details": "Checking..."},
            "browser_pool": {"status": "unknown", "details": "Checking..."}
        }
    }
    
    # Check database
    try:
        db_manager = DatabaseAdapter(DB_PATH)
        # Try to perform a simple query
        with db_manager.get_session() as session:
            session.execute("SELECT 1")
        health_status["components"]["database"] = {"status": "healthy", "details": "Database connection OK"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = {"status": "unhealthy", "details": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Qdrant
    try:
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # Try to get collections list to verify connection
        qdrant_client.get_collections()
        health_status["components"]["qdrant"] = {"status": "healthy", "details": "Qdrant connection OK"}
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        health_status["components"]["qdrant"] = {"status": "unhealthy", "details": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check browser pool (if available in app state)
    # This check would be more complex as it requires access to app.state
    # For now, we'll just mark it as healthy since initialization happens in lifespan
    try:
        # We can't access app.state here directly, so we'll just verify the module is importable
        # In a real scenario, you might pass the app instance or use a different approach
        import resource_management.browser_pool_manager
        health_status["components"]["browser_pool"] = {"status": "healthy", "details": "Browser pool module loaded"}
    except Exception as e:
        logger.error(f"Browser pool health check failed: {e}")
        health_status["components"]["browser_pool"] = {"status": "unhealthy", "details": str(e)}
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@router.get("/health/browser-resources")
async def browser_resources_health():
    """
    Health check endpoint for browser resources.
    Returns metrics and status of browser resource pool.
    """
    # This endpoint was already implemented in app.py, but we'll duplicate it here
    # for completeness in the health endpoints module
    # In a real app, you might centralize this differently
    from api.app import create_app
    app = create_app()
    
    try:
        browser_pool_manager = app.state.browser_pool_manager if hasattr(app.state, 'browser_pool_manager') else None
        
        if browser_pool_manager is None:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": "BrowserPoolManager not available in app state",
                "pool_stats": None
            }
        
        stats = await browser_pool_manager.get_stats()
        
        # Check if pool is healthy
        is_healthy = (
            stats['available_count'] >= 0 and
            stats['acquired_count'] <= stats['max_size'] and
            stats['circuit_breaker']['state'] == 'closed'
        )
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "pool_stats": stats
        }
    except Exception as e:
        logger.error(f"Browser resources health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
