"""
Main entry point for the FIPI Parser application.
This script orchestrates the scraping process:
1. Loads configuration.
2. Fetches available subjects from the FIPI website.
3. Provides a console interface for the user to select a subject.
4. Scrapes pages for the selected subject.
5. Processes and saves the data using dedicated modules.
6. Starts the API server in a separate thread.
"""
import config
from scraper import fipi_scraper
from processors import html_renderer, json_saver
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
from api.answer_api import create_app
from utils.database_manager import DatabaseManager  # NEW: Import DatabaseManager
from pathlib import Path
from datetime import datetime
import threading
import uvicorn
import time
import asyncio

def start_api_server(app, host="127.0.0.1", port=8000):
    """Starts the Uvicorn server in a separate thread."""
    print(f"Starting API server on {host}:{port}...")
    uvicorn.run(app, host=host, port=port, log_level="info")

def get_user_selection(subjects_dict):
    """
    Presents a console interface for the user to select a subject.
    Args:
        subjects_dict (dict): A dictionary mapping project IDs to subject names.
    Returns:
        tuple: The selected (project_id, subject_name).
    """
    print("\n--- Available Subjects ---")
    options = list(subjects_dict.items())
    for i, (proj_id, name) in enumerate(options, 1):
        print(f"{i}. {name} (ID: {proj_id})")

    while True:
        try:
            choice = int(input("\nSelect a subject by number: "))
            if 1 <= choice <= len(options):
                proj_id, subject_name = options[choice - 1]
                print(f"You selected: {subject_name} (ID: {proj_id})")
                return proj_id, subject_name
            else:
                print(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def main():
    """
    Main function to run the FIPI parser.
    """
    print("--- FIPI Parser Started ---")

    # 1. Initialize Scraper to get subjects
    scraper = fipi_scraper.FIPIScraper(
        base_url=config.FIPI_QUESTIONS_URL, # URL for scrape_page
        subjects_url=config.FIPI_SUBJECTS_URL # URL for get_projects
    )

    print("Fetching available subjects...")
    try:
        subjects = scraper.get_projects()
        if not subjects:
            print("Warning: No subjects found on the page.")
            return
    except Exception as e:
        print(f"Error fetching subjects: {e}")
        return

    # 2. Get user selection
    selected_proj_id, selected_subject_name = get_user_selection(subjects)

    # 3. Create run-specific output folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize subject name for use in path
    safe_subject_name = "".join(c for c in selected_subject_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    run_folder = config.DATA_ROOT / config.OUTPUT_DIR / f"{safe_subject_name}_{selected_proj_id}" / f"run_{timestamp}"
    run_folder.mkdir(parents=True, exist_ok=True)
    print(f"Data will be saved to: {run_folder}")

    # --- NEW: Initialize API components ---
    storage = LocalStorage(run_folder / "answers.json")
    checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)
    app = create_app(storage, checker)

    # --- NEW: Start API server in a separate thread ---
    api_host = "127.0.0.1"
    api_port = 8000
    api_thread = threading.Thread(target=start_api_server, args=(app, api_host, api_port), daemon=True)
    api_thread.start()
    print(f"API server started in background. Waiting for server to be ready on {api_host}:{api_port}...")
    time.sleep(3) # Give the server a moment to start up
    print("API server should be ready.")

    # 4. Initialize processors - передаем storage в html_proc
    html_proc = html_renderer.HTMLRenderer(storage=storage) # NEW: Pass storage
    json_proc = json_saver.JSONSaver()
    # NEW: Initialize DatabaseManager instead of ProblemStorage
    db_manager = DatabaseManager(str(run_folder / "fipi_data.db")) # NEW: Initialize DatabaseManager
    db_manager.initialize_db() # NEW: Initialize database tables

    # 5. Scrape and process pages - ВОССТАНОВЛЕНО: полный список страниц
    page_list = ["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)]

    for page_name in page_list:
        print(f"Processing page: {page_name} for subject '{selected_subject_name}'...")
        try:
            # Scrape raw data for the page - NEW: receives (problems, scraped_data)
            problems, scraped_data = scraper.scrape_page(selected_proj_id, page_name, run_folder)
            if not scraped_data.get("blocks_html"): # ИСПРАВЛЕНО: Проверяем blocks_html в словаре scraped_data
                print(f"  Warning: No data scraped for page {page_name}. Skipping.")
                continue
            
            # NEW: Save Problems using DatabaseManager instead of ProblemStorage
            db_manager.save_problems(problems) # NEW: Use DatabaseManager
            print(f"  Saved {len(problems)} problems to SQLite database for page {page_name}.")

            # --- Process and save HTML for the entire PAGE (as before) ---
            # NEW: Передаем page_name в render, чтобы он мог получить initial_state
            html_content = html_proc.render(scraped_data, page_name=page_name)
            html_file_path = run_folder / page_name / f"{page_name}.html" # HTML в подпапку
            html_file_path.parent.mkdir(parents=True, exist_ok=True) # Убедиться, что подпапка существует
            html_proc.save(html_content, html_file_path)

            # --- Process and save HTML for EACH BLOCK separately ---
            # ИСПРАВЛЕНО: Добавляем цикл по blocks_html
            blocks_html = scraped_data.get("blocks_html", [])
            task_metadata = scraped_data.get("task_metadata", [])
            for block_idx, block_content in enumerate(blocks_html):
                # NEW: Получаем task_id и form_id из метаданных
                metadata = task_metadata[block_idx] if block_idx < len(task_metadata) else {}
                task_id = metadata.get('task_id', '')
                form_id = metadata.get('form_id', '')
                # Generate HTML for a single block using the new method
                # ИСПРАВЛЕНО: Передаём asset_path_prefix="../assets" для коррекции путей
                # NEW: Передаем page_name и block_idx для получения initial_state для конкретного блока
                # NEW: Передаем task_id и form_id в render_block
                block_html_content = html_proc.render_block(
                    block_content,
                    block_idx,
                    asset_path_prefix="../assets",
                    page_name=page_name,
                    task_id=task_id, # NEW: Pass task_id
                    form_id=form_id  # NEW: Pass form_id
                )
                # Define path for the block's HTML file
                block_html_file_path = run_folder / page_name / "blocks" / f"block_{block_idx}_{page_name}.html" # HTML блока в подпапку 'blocks'
                block_html_file_path.parent.mkdir(parents=True, exist_ok=True) # Убедиться, что подпапка 'blocks' существует
                # Save the block's HTML
                html_proc.save(block_html_content, block_html_file_path)
                print(f"  Saved block HTML: {block_html_file_path.relative_to(run_folder)}")

            # Process and save JSON - ИСПРАВЛЕНО: сохраняем в подпапку page_name
            json_file_path = run_folder / page_name / f"{page_name}.json" # JSON в подпапку
            json_proc.save(scraped_data, json_file_path)
            print(f"  Saved Page HTML: {html_file_path.relative_to(run_folder)}, JSON: {json_file_path.relative_to(run_folder)}")
        except Exception as e:
            print(f"  Error processing page {page_name}: {e}")
            # Optionally log error to a file within run_folder
            error_log_path = run_folder / "error_log.txt"
            with open(error_log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"Page {page_name}: {e}\n")
            continue # Skip to the next page

    print(f"\n--- Parsing completed for '{selected_subject_name}'. Data saved in: {run_folder} ---")
    print(f"API server is running on http://{api_host}:{api_port}")
    print("Press Enter to stop the API server and exit...")
    input() # Wait for user input before exiting
    print("Exiting...")

if __name__ == "__main__":
    main()
