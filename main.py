"""
Main entry point for the FIPI Parser application.
This script now ALWAYS starts the API servers, loading from existing data.
Scraping and other management tasks are intended to be triggered via the web UI.
"""
import config
from scraper import fipi_scraper
from processors import html_renderer, json_saver
from utils.database_manager import DatabaseManager # NEW: Import DatabaseManager
from utils.answer_checker import FIPIAnswerChecker # NEW: Import AnswerChecker
from utils.local_storage import LocalStorage # NEW: Import LocalStorage
from api.answer_api import create_app # NEW: Import answer API app factory
from api.core_api import create_core_app # NEW: Import core API app factory
from utils.logging_config import setup_logging # NEW: Import logging setup
import logging # NEW: Import logging
from pathlib import Path
from datetime import datetime
import threading # NEW: Import threading for API server and scraping
import time # NEW: Import time for waiting
import uvicorn # NEW: Import uvicorn to run the API server
import os # NEW: Import os for graceful shutdown
import glob # NEW: Import glob to find latest run folder
import asyncio # NEW: Import asyncio for running scraper asynchronously

# Global variable to track scraping status (simple approach)
scraping_status = {"is_running": False, "current_subject": None, "progress": 0}

def find_existing_subjects():
    """
    Scans the problems directory to find subjects with existing data.
    Returns:
        dict: A dictionary mapping sanitized subject names to the path of their latest run folder.
    """
    logger = logging.getLogger(__name__)
    subjects_data = {}
    search_pattern = str(config.DATA_ROOT / config.OUTPUT_DIR / "*")
    subject_folders = glob.glob(search_pattern)

    for folder_path in subject_folders:
        folder_name = Path(folder_path).name
        # Extract base subject name (everything before the first underscore followed by hex)
        # This assumes the format is "SubjectName_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        parts = folder_name.split('_')
        if len(parts) > 1 and len(parts[-1]) == 32 and all(c in '0123456789ABCDEFabcdef' for c in parts[-1]):
            base_name = '_'.join(parts[:-1])
        else:
            base_name = folder_name # Fallback if format doesn't match

        run_search_pattern = str(Path(folder_path) / "run_*")
        run_folders = glob.glob(run_search_pattern)
        if run_folders:
            latest_run = max(run_folders, key=os.path.getctime)
            subjects_data[base_name] = Path(latest_run)
            logger.info(f"Found existing data for subject '{base_name}' in: {latest_run}")

    return subjects_data

def find_latest_run_folder(subject_name):
    """Finds the latest run folder for a given subject."""
    logger = logging.getLogger(__name__)
    safe_subject_name = "".join(c for c in subject_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    search_pattern = str(config.DATA_ROOT / config.OUTPUT_DIR / f"{safe_subject_name}_*" / "run_*")
    folders = glob.glob(search_pattern)
    if not folders:
        logger.error(f"No run folders found for subject '{subject_name}' matching pattern '{search_pattern}'")
        return None

    latest_folder = max(folders, key=os.path.getctime)
    logger.info(f"Found latest run folder for '{subject_name}': {latest_folder}")
    return Path(latest_folder)

def run_api_only(selected_subject_name, run_folder_path):
    """
    Runs the API servers without scraping, loading dependencies from a specified run folder.
    """
    global scraping_status # NEW: Access global status
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to start API servers for subject: {selected_subject_name} using folder: {run_folder_path}")

    run_folder = Path(run_folder_path)
    db_path = run_folder / "fipi_data.db"
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        print(f"Error: Database file not found: {db_path}")
        return

    # NEW: Initialize DatabaseManager from existing DB
    logger.info(f"Initializing DatabaseManager from: {db_path}") # NEW: Log initialization
    db_manager = DatabaseManager(str(db_path))

    # NEW: Initialize LocalStorage from existing file
    storage_file = run_folder / "answers.json"
    logger.info(f"Initializing LocalStorage from: {storage_file}") # NEW: Log initialization
    storage = LocalStorage(storage_file)

    # NEW: Initialize AnswerChecker (still needs base URL for API calls)
    logger.info("Initializing FIPIAnswerChecker") # NEW: Log initialization
    checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)

    # NEW: Create API applications
    logger.info("Creating Answer API application") # NEW: Log app creation
    answer_app = create_app(db_manager, checker) # NEW: Pass db_manager and checker to Answer API

    logger.info("Creating Core API application") # NEW: Log app creation
    core_app = create_core_app(db_manager, storage, checker, scraping_status) # NEW: Pass scraping_status too

    # NEW: Define a target function for the thread that handles server startup
    def run_server(app, host, port, name):
        try:
            logger.info(f"Attempting to start {name} server on {host}:{port}...")
            uvicorn.run(app, host=host, port=port, log_level="info")
        except OSError as e:
            if e.errno == 98: # Address already in use
                logger.error(f"Failed to start {name} server on {host}:{port}: Address already in use ({e.errno}).")
                print(f"ERROR: Cannot start {name} server on {host}:{port}. Address already in use. Please stop the other process using this port first.")
                os._exit(1) # Exit the script if port is in use
            else:
                logger.error(f"Failed to start {name} server on {host}:{port}: {e}")
                print(f"ERROR: Cannot start {name} server on {host}:{port}. Reason: {e}")
                os._exit(1) # Exit the script for any other error
        except Exception as e:
            logger.error(f"Unexpected error in {name} server thread: {e}", exc_info=True)
            print(f"ERROR: Unexpected error in {name} server thread: {e}")
            os._exit(1) # Exit the script for any other error

    # NEW: Start API servers in background threads using the target function
    # Start Answer API on port 8000
    logger.info("Starting Answer API server in background thread...")
    answer_api_thread = threading.Thread(
        target=run_server,
        args=(answer_app, "127.0.0.1", 8000, "Answer API")
    )
    answer_api_thread.daemon = True # NEW: Daemon thread so it closes with main script
    answer_api_thread.start()

    # NEW: Brief wait to allow the thread to attempt startup and potentially log the error before proceeding
    time.sleep(1)
    logger.info("Answer API server startup process initiated in background thread.")

    # Start Core API on a different port, e.g., 8001
    logger.info("Starting Core API server in background thread...")
    core_api_thread = threading.Thread(
        target=run_server,
        args=(core_app, "127.0.0.1", 8001, "Core API")
    )
    core_api_thread.daemon = True # NEW: Daemon thread so it closes with main script
    core_api_thread.start()

    # NEW: Brief wait to allow the thread to attempt startup and potentially log the error before proceeding
    time.sleep(1)
    logger.info("Core API server startup process initiated in background thread.")

    print(f"\n--- API servers started for '{selected_subject_name}' using data from: {run_folder} ---")
    print(f"--- Web UI available at: https://ixem.duckdns.org ---")
    logger.info(f"API servers started for '{selected_subject_name}' using data from: {run_folder}")

    # NEW: Keep the main thread alive to allow API servers to run
    try:
        print("Press Ctrl+C to stop the API servers and exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        logger.info("Shutdown signal received.")
        os._exit(0) # Exit the script when Ctrl+C is pressed


def run_scraping_async(proj_id, subject_name, total_pages_override=None):
    """
    Runs the scraping process in a separate thread.
    Updates the global scraping_status.
    """
    global scraping_status
    logger = logging.getLogger(__name__)
    scraping_status["is_running"] = True
    scraping_status["current_subject"] = subject_name
    scraping_status["progress"] = 0

    try:
        logger.info(f"Scraping started for subject '{subject_name}' (ID: {proj_id}) in background thread.")
        print(f"Scraping started for '{subject_name}'...")

        # --- Original scraping flow from main() ---
        # 1. Initialize Scraper
        scraper = fipi_scraper.FIPIScraper(
            base_url=config.FIPI_QUESTIONS_URL,
            subjects_url=config.FIPI_SUBJECTS_URL
        )

        # 3. Create run-specific output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_subject_name = "".join(c for c in subject_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        run_folder = config.DATA_ROOT / config.OUTPUT_DIR / f"{safe_subject_name}_{proj_id}" / f"run_{timestamp}"
        run_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Scraping data will be saved to: {run_folder}")
        print(f"Scraping data will be saved to: {run_folder}")

        # NEW: Allow override for total pages (for testing or specific subjects)
        total_pages = total_pages_override if total_pages_override is not None else config.TOTAL_PAGES

        # NEW: Initialize DatabaseManager for this run
        logger.info("Initializing DatabaseManager for scraping run")
        db_manager = DatabaseManager(str(run_folder / "fipi_data.db"))
        db_manager.initialize_db()

        # NEW: Initialize LocalStorage for this run
        logger.info("Initializing LocalStorage for scraping run")
        storage = LocalStorage(run_folder / "answers.json")

        # NEW: Initialize AnswerChecker for this run (likely not needed for scraping, but kept if needed later)
        checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)

        # 4. Initialize processors
        html_proc = html_renderer.HTMLRenderer(db_manager=db_manager) # Use db_manager
        json_proc = json_saver.JSONSaver()

        # 5. Scrape and process pages
        page_list = ["init"] + [str(i) for i in range(1, total_pages + 1)]
        total_pages_to_process = len(page_list)
        for idx, page_name in enumerate(page_list):
            print(f"Processing page: {page_name} for subject '{subject_name}'... ({idx + 1}/{total_pages_to_process})")
            logger.info(f"Processing page: {page_name} for subject '{subject_name}'... ({idx + 1}/{total_pages_to_process})")
            scraping_status["progress"] = int(((idx + 1) / total_pages_to_process) * 100)

            try:
                problems, scraped_data = scraper.scrape_page(proj_id, page_name, run_folder)
                if not scraped_data:
                    logger.warning(f"Warning: No data scraped for page {page_name}. Skipping.")
                    print(f"  Warning: No data scraped for page {page_name}. Skipping.")
                    continue

                # NEW: Save the scraped problems using DatabaseManager
                logger.info(f"Saving {len(problems)} problems for page {page_name} to database...")
                db_manager.save_problems(problems)

                # --- Process and save HTML for the entire PAGE ---
                html_content = html_proc.render(scraped_data, page_name)
                html_file_path = run_folder / page_name / f"{page_name}.html"
                html_file_path.parent.mkdir(parents=True, exist_ok=True)
                html_proc.save(html_content, html_file_path)
                logger.info(f"Saved Page HTML: {html_file_path.relative_to(run_folder)}")

                # --- Process and save HTML for EACH BLOCK separately ---
                blocks_html = scraped_data.get("blocks_html", [])
                task_metadata = scraped_data.get("task_metadata", [])
                for block_idx, block_content in enumerate(blocks_html):
                    metadata = task_metadata[block_idx] if block_idx < len(task_metadata) else {}
                    task_id = metadata.get('task_id', '')
                    form_id = metadata.get('form_id', '')

                    block_html_content = html_proc.render_block(
                        block_content, block_idx,
                        asset_path_prefix="../../assets",
                        task_id=task_id,
                        form_id=form_id,
                        page_name=page_name
                    )
                    block_html_file_path = run_folder / page_name / "blocks" / f"block_{block_idx}_{page_name}.html"
                    block_html_file_path.parent.mkdir(parents=True, exist_ok=True)
                    html_proc.save(block_html_content, block_html_file_path)
                    logger.info(f"Saved block HTML: {block_html_file_path.relative_to(run_folder)}")
                    print(f"  Saved block HTML: {block_html_file_path.relative_to(run_folder)}")

                # Process and save JSON
                json_file_path = run_folder / page_name / f"{page_name}.json"
                json_proc.save(scraped_data, json_file_path)
                logger.info(f"Saved JSON: {json_file_path.relative_to(run_folder)}")
                print(f"  Saved Page HTML: {html_file_path.relative_to(run_folder)}, JSON: {json_file_path.relative_to(run_folder)}")

            except Exception as e:
                logger.error(f"Error processing page {page_name}: {e}", exc_info=True)
                print(f"  Error processing page {page_name}: {e}")
                error_log_path = run_folder / "error_log.txt"
                with open(error_log_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"Page {page_name}: {e}\n")
                # continue # Let it finish other pages or stop?

        print(f"\n--- Parsing completed for '{subject_name}'. Data saved in: {run_folder} ---")
        logger.info(f"Parsing completed for '{subject_name}'. Data saved in: {run_folder}")

    except Exception as e:
        logger.error(f"Error during scraping thread for '{subject_name}': {e}", exc_info=True)
        print(f"Error during scraping thread for '{subject_name}': {e}")

    finally:
        scraping_status["is_running"] = False
        scraping_status["current_subject"] = None
        scraping_status["progress"] = 0
        print(f"Scraping thread for '{subject_name}' finished.")


def main():
    """
    Main function to run the FIPI parser.
    ALWAYS starts API servers, loading from the first detected subject or a default.
    Scraping is managed via the web UI.
    """
    # NEW: Setup logging first
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)
    logger.info("FIPI Parser Started (API Mode)")

    # Check for existing subjects
    existing_subjects = find_existing_subjects()
    has_existing_data = bool(existing_subjects)

    if has_existing_data:
        # Use the first found subject as the default for the API
        default_subject_name = list(existing_subjects.keys())[0]
        default_run_folder = existing_subjects[default_subject_name]
        print(f"Found existing data for subjects: {list(existing_subjects.keys())}")
        print(f"Starting API with default subject: {default_subject_name}")
    else:
        print("No existing subject data found in problems/ directory.")
        # You might want to exit here or start with a minimal API/core that only allows scraping setup
        # For now, let's assume we need at least one subject to start the full API
        print("Please run scraping first using the CLI mode (option 1 in previous version) or set up data manually.")
        print("Exiting.")
        return

    # Start the API with the default subject (or first found)
    run_api_only(default_subject_name, default_run_folder)


if __name__ == "__main__":
    main()
