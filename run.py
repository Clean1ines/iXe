"""
Unified entry point for the FIPI API.

This module serves as the main application factory for the FastAPI backend.
It supports both local development and Render.com deployment by reading
the PORT environment variable. The application is configured with
default settings suitable for production (no reload, single worker).

Attributes:
    app: The main FastAPI application instance.
"""

from api.app import create_app

app = create_app()

if __name__ == "__main__":
    """
    Runs the application using Uvicorn ASGI server.

    This block is executed only when the script is run directly.
    It reads the PORT from environment variables (defaulting to 8000)
    and binds to all interfaces (0.0.0.0) for production readiness.
    """
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
