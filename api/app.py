# api/app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import FRONTEND_URL
from api.endpoints import subjects, quiz, answer, plan
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="FIPI Core API",
        description="Unified API for ЕГЭ preparation platform",
        version="1.0.0",
        openapi_url="/openapi.yaml",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    origins = [
        "https://ixe.onrender.com",      # фронтенд на Render
        "https://ixe-core.onrender.com", # сам себя (health-check)
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
        logger.warning(f"HTTPException {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception for {request.method} {request.url}: {exc}", exc_info=True)
        # В production лучше не возвращать traceback
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    # ---

    app.include_router(subjects.router, prefix="/api")
    app.include_router(quiz.router, prefix="/api")
    app.include_router(answer.router, prefix="/api")
    app.include_router(plan.router, prefix="/api")

    @app.get("/")
    async def root():
        return {"message": "FIPI API is running"}

    return app
