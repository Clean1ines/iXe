from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.scrape_tasks import CLIScraper

app = FastAPI()

class ScrapeRequest(BaseModel):
    subject: str

@app.post("/scrape/{subject}")
async def scrape_subject(subject: str, background_tasks: BackgroundTasks):
    # Validate subject if needed
    cli_scraper = CLIScraper()
    available_subjects = cli_scraper.get_available_subjects()
    if subject not in available_subjects:
        raise HTTPException(status_code=400, detail=f"Subject {subject} not available")

    # Run scraping in background
    background_tasks.add_task(run_scraping, subject)
    return {"message": f"Scraping started for subject: {subject}"}

async def run_scraping(subject: str):
    cli_scraper = CLIScraper()
    # This is a simplified call, you might need to adjust based on how you want to handle subject keys vs names
    # and how the original CLIScraper was designed to be called programmatically vs interactively
    # For now, we'll simulate selecting a single subject for scraping
    await cli_scraper.parallel_scrape_logic([subject], None) # This needs adjustment for BrowserPoolManager

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
