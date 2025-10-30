from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import FRONTEND_URL
from api.endpoints import subjects, quiz, answer, plan

def create_app() -> FastAPI:
    app = FastAPI(
        title="FIPI Core API",
        description="Unified API for ЕГЭ preparation platform",
        version="1.0.0"
    )

    # CORS: разрешаем фронтенд на Render и локальную разработку
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

    # Подключаем роутеры
    app.include_router(subjects.router, prefix="/api")
    app.include_router(quiz.router, prefix="/api")
    app.include_router(answer.router, prefix="/api")
    app.include_router(plan.router, prefix="/api")

    @app.get("/")
    async def root():
        return {"message": "FIPI API is running"}

    return app
