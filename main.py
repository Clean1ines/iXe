"""
Main entry point for the FIPI Parser API application.

This script initializes and runs the FastAPI application for the
FIPI Parser web service. It no longer contains scraping logic,
which has been moved to scripts/scrape_tasks.py.
"""

import asyncio
from fastapi import FastAPI
from utils.logging_config import setup_logging

# Initialize logging
setup_logging(level="INFO")

# Create FastAPI application instance
app = FastAPI(
    title="FIPI Parser API",
    description="API for accessing FIPI educational tasks data",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint for the API."""
    return {"message": "Welcome to FIPI Parser API"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Add other API routes here as needed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
