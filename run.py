"""
Unified entry point for the FIPI API.
Supports local development and Render.com deployment via environment variables.
"""

from api.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os

    # Render.com задаёт PORT автоматически
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"

    uvicorn.run(
        "run:app",
        host=host,
        port=port,
        reload=False,  # Render: no reload in production
        workers=1,
    )
