# api/app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import FRONTEND_URL
from api.endpoints import subjects, quiz, answer, plan, block
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application instance.

    Sets up CORS, exception handlers, and includes API routers.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    app = FastAPI(
        title="FIPI Core API",
        description="Unified API for ЕГЭ preparation platform",
        version="1.0.0",
        openapi_url="/openapi.yaml",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    origins = [
        "https://ixe.onrender.com",
        "https://ixe-core.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Централизованная обработка исключений ---
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handles HTTP exceptions globally.
        """
        logger.warning(f"HTTPException {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Handles unhandled exceptions globally.
        """
        logger.error(f"Unhandled exception for {request.method} {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    # ---

    app.include_router(subjects.router, prefix="/api")
    app.include_router(quiz.router, prefix="/api")
    app.include_router(answer.router, prefix="/api")
    app.include_router(plan.router, prefix="/api")
    app.include_router(block.router, prefix="/api")

    @app.get("/")
    async def root():
        """
        Health check endpoint.
        """
        return {"message": "FIPI API is running"}

    return app
