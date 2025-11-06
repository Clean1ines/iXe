from fastapi import APIRouter
from utils.browser_pool_manager import BrowserPoolManager
from utils.browser_manager import BrowserManager
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instance reference for health checks
browser_pool = None

def set_browser_pool(pool: BrowserPoolManager):
    global browser_pool
    browser_pool = pool

@router.get("/health")
async def health_check():
    """Health check endpoint for automation service"""
    try:
        status = {
            "status": "healthy",
            "service": "automation-service",
            "checks": {
                "browser_pool": "not_available",
                "fipi_connectivity": "not_tested"
            }
        }
        
        if browser_pool:
            # Check browser pool status
            pool_size = browser_pool.pool_size
            available_count = browser_pool._queue.qsize()
            status["checks"]["browser_pool"] = f"available: {available_count}/{pool_size}"
            
            # Perform basic browser test if possible
            try:
                test_browser = await browser_pool.get_available_browser()
                await browser_pool.return_browser(test_browser)
                status["checks"]["browser_test"] = "ok"
            except Exception as e:
                status["checks"]["browser_test"] = f"error: {str(e)}"
                status["status"] = "degraded"
        
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@router.get("/health/extended")
async def extended_health_check():
    """Extended health check with detailed browser pool information"""
    try:
        status = {
            "status": "healthy",
            "service": "automation-service",
            "timestamp": asyncio.get_event_loop().time(),
            "details": {
                "browser_pool": {
                    "pool_size": 0,
                    "available": 0,
                    "request_counts": {}
                }
            }
        }
        
        if browser_pool:
            status["details"]["browser_pool"] = {
                "pool_size": browser_pool.pool_size,
                "available": browser_pool._queue.qsize(),
                "max_requests_per_context": browser_pool.max_requests_per_context,
                "request_counts": browser_pool._request_counts
            }
        
        return status
    except Exception as e:
        logger.error(f"Extended health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
