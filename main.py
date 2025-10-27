"""
Main entry point for the FIPI Parser application.
This script orchestrates the scraping process:
1. Loads configuration.
2. Fetches available subjects from the FIPI website.
3. Provides a console interface for the user to select a subject.
4. Scrapes pages for the selected subject.
5. Processes and saves the data using dedicated modules.
OR
1. Option to run only the API servers without scraping, loading from existing data.
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
import threading # NEW: Import threading for API server
import time # NEW: Import time for waiting
import uvicorn # NEW: Import uvicorn to run the API server
import os # NEW: Import os for graceful shutdown
import glob # NEW: Import glob to find latest run folder

def get_user_selection(subjects_dict):
    """
    Presents a console interface for the user to select a subject.
    Args:
        subjects_dict (dict): A dictionary mapping project IDs to subject names.
    Returns:
        tuple: The selected (project_id, subject_name).
    """
    logger = logging.getLogger(__name__) # NEW: Get logger for this function
    logger.info("Presenting subject selection interface") # NEW: Log the action
    print("\n--- Available Subjects ---")
    options = list(subjects_dict.items())
    for i, (proj_id, name) in enumerate(options, 1):
        print(f"{i}. {name} (ID: {proj_id})")

    while True:
        try:
            choice = int(input("\nSelect a subject by number: "))
            if 1 <= choice <= len(options):
                proj_id, subject_name = options[choice - 1]
                logger.info(f"User selected: {subject_name} (ID: {proj_id})") # NEW: Log selection
                print(f"You selected: {subject_name} (ID: {proj_id})")
                return proj_id, subject_name
            else:
                print(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def find_latest_run_folder(subject_name):
    """Finds the latest run folder for a given subject."""
    logger = logging.getLogger(__name__)
    safe_subject_name = "".join(c for c in subject_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    search_pattern = str(config.DATA_ROOT / config.OUTPUT_DIR / f"{safe_subject_name}_*" / "run_*")
    folders = glob.glob(search_pattern)
    if not folders:
        logger.error(f"No run folders found for subject '{subject_name}' matching pattern '{search_pattern}'")
        print(f"Error: No run folders found for subject '{subject_name}'.")
        return None

    latest_folder = max(folders, key=os.path.getctime)
    logger.info(f"Found latest run folder for '{subject_name}': {latest_folder}")
    return Path(latest_folder)

def run_api_only(selected_subject_name):
    """
    Runs the API servers without scraping, loading dependencies from the latest run folder.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to start API servers for subject: {selected_subject_name}")

    run_folder = find_latest_run_folder(selected_subject_name)
    if not run_folder:
        return

    db_path = run_folder / "fipi_data.db"
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        print(f"Error: Database file not found: {db_path}")
        return

    # NEW: Initialize DatabaseManager from existing DB
    logger.info(f"Initializing DatabaseManager from: {db_path}") # NEW: Log initialization
    db_manager = DatabaseManager(str(db_path))
    # Note: We assume DB is already initialized from a previous run, so initialize_db() might not be necessary here,
    # but calling it is safe if it only creates tables if they don't exist.
    # db_manager.initialize_db()

    # NEW: Initialize LocalStorage from existing file
    storage_file = run_folder / "answers.json"
    logger.info(f"Initializing LocalStorage from: {storage_file}") # NEW: Log initialization
    storage = LocalStorage(storage_file) # NEW: Use run_folder for storage

    # NEW: Initialize AnswerChecker (still needs base URL for API calls, might be okay for checking cached answers too)
    logger.info("Initializing FIPIAnswerChecker") # NEW: Log initialization
    checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)

    # NEW: Create API applications
    logger.info("Creating Answer API application") # NEW: Log app creation
    answer_app = create_app(db_manager, checker) # NEW: Pass db_manager and checker to Answer API

    logger.info("Creating Core API application") # NEW: Log app creation
    core_app = create_core_app(db_manager, storage, checker) # NEW: Pass dependencies to Core API

    # NEW: Define a target function for the thread that handles server startup
    def run_server(app, host, port, name):
        try:
            logger.info(f"Attempting to start {name} server on {host}:{port}...")
            uvicorn.run(app, host=host, port=port, log_level="info")
        except OSError as e:
            if e.errno == 98: # Address already in use
                logger.error(f"Failed to start {name} server on {host}:{port}: Address already in use ({e.errno}).")
                print(f"ERROR: Cannot start {name} server on {host}:{port}. Address already in use. Please stop the other process using this port first.")
                os._exit(1) # Exit the script if port is use
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


def main():
    """
    Main function to run the FIPI parser.
    """
    # NEW: Setup logging first
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)
    logger.info("FIPI Parser Started")

    print("Choose an action:")
    print("1. Scrape and process a subject (default behavior)")
    print("2. Run API servers only (using existing data)")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "2":
        subject_name = input("Enter the subject name (e.g., 'ЕГЭ Математика'): ").strip()
        run_api_only(subject_name)
        return
    elif choice != "1":
        print("Invalid choice. Defaulting to scraping (option 1).")

    # --- Original scraping flow starts here ---
    # 1. Initialize Scraper to get subjects
    logger.info("Initializing FIPIScraper")
    scraper = fipi_scraper.FIPIScraper(
        base_url=config.FIPI_QUESTIONS_URL, # URL for scrape_page
        subjects_url=config.FIPI_SUBJECTS_URL # URL for get_projects
    )

    print("Fetching available subjects...")
    logger.info("Fetching available subjects...")
    try:
        subjects = scraper.get_projects()
        if not subjects:
            logger.warning("Warning: No subjects found on the page.")
            print("Warning: No subjects found on the page.")
            return
    except Exception as e:
        logger.error(f"Error fetching subjects: {e}", exc_info=True)
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
    logger.info(f"Data will be saved to: {run_folder}") # NEW: Log run folder creation
    print(f"Data will be saved to: {run_folder}")

    # NEW: Initialize DatabaseManager
    logger.info("Initializing DatabaseManager") # NEW: Log initialization
    db_manager = DatabaseManager(str(run_folder / "fipi_data.db"))
    db_manager.initialize_db() # NEW: Create tables if they don't exist

    # NEW: Initialize LocalStorage
    logger.info("Initializing LocalStorage") # NEW: Log initialization
    storage = LocalStorage(run_folder / "answers.json") # NEW: Use run_folder for storage

    # NEW: Initialize AnswerChecker
    logger.info("Initializing FIPIAnswerChecker") # NEW: Log initialization
    checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)

    # NEW: Create API applications
    logger.info("Creating Answer API application") # NEW: Log app creation
    answer_app = create_app(db_manager, checker) # NEW: Pass db_manager and checker to Answer API

    logger.info("Creating Core API application") # NEW: Log app creation
    core_app = create_core_app(db_manager, storage, checker) # NEW: Pass dependencies to Core API

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

    # 4. Initialize processors
    # OLD: html_proc = html_renderer.HTMLRenderer(storage=storage) # NEW: Pass storage
    # CHANGED: Pass db_manager instead of storage
    html_proc = html_renderer.HTMLRenderer(db_manager=db_manager) # NEW: Pass db_manager

    json_proc = json_saver.JSONSaver()

    # 5. Scrape and process pages
    page_list = ["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)]
    for page_name in page_list:
        print(f"Processing page: {page_name} for subject '{selected_subject_name}'...")
        logger.info(f"Processing page: {page_name} for subject '{selected_subject_name}'...") # NEW: Log page processing
        try:
            # Scrape raw data for the page - ИСПРАВЛЕНО: передаем run_folder
            # CHANGED: scrape_page now returns (problems, scraped_data)
            problems, scraped_data = scraper.scrape_page(selected_proj_id, page_name, run_folder)
            if not scraped_data:
                logger.warning(f"Warning: No data scraped for page {page_name}. Skipping.") # NEW: Log warning
                print(f"  Warning: No data scraped for page {page_name}. Skipping.")
                continue

            # NEW: Save the scraped problems using DatabaseManager
            logger.info(f"Saving {len(problems)} problems for page {page_name} to database...") # NEW: Log saving
            db_manager.save_problems(problems)

            # --- Process and save HTML for the entire PAGE (as before) ---
            # CHANGED: render now requires page_name
            html_content = html_proc.render(scraped_data, page_name) # NEW: Pass page_name
            html_file_path = run_folder / page_name / f"{page_name}.html" # HTML в подпапку
            html_file_path.parent.mkdir(parents=True, exist_ok=True) # Убедиться, что подпапка существует
            html_proc.save(html_content, html_file_path)
            logger.info(f"Saved Page HTML: {html_file_path.relative_to(run_folder)}") # NEW: Log saving

            # --- Process and save HTML for EACH BLOCK separately ---
            # ИСПРАВЛЕНО: Добавляем цикл по blocks_html
            blocks_html = scraped_data.get("blocks_html", [])
            task_metadata = scraped_data.get("task_metadata", []) # NEW: Get task metadata
            for block_idx, block_content in enumerate(blocks_html):
                # NEW: Get task_id and form_id for the current block from metadata
                metadata = task_metadata[block_idx] if block_idx < len(task_metadata) else {}
                task_id = metadata.get('task_id', '')
                form_id = metadata.get('form_id', '')

                # Generate HTML for a single block using the new method
                # ИСПРАВЛЕНО: Передаём asset_path_prefix="../../assets" для коррекции путей
                # CHANGED: render_block now requires task_id, form_id, page_name for initial state
                block_html_content = html_proc.render_block(
                    block_content, block_idx,
                    asset_path_prefix="../../assets", # ИСПРАВЛЕНО: Путь относительно init/blocks/
                    task_id=task_id, # NEW: Pass task_id
                    form_id=form_id, # NEW: Pass form_id
                    page_name=page_name # NEW: Pass page_name for potential state loading
                )
                # Define path for the block's HTML file
                block_html_file_path = run_folder / page_name / "blocks" / f"block_{block_idx}_{page_name}.html" # HTML блока в подпапку 'blocks'
                block_html_file_path.parent.mkdir(parents=True, exist_ok=True) # Убедиться, что подпапка 'blocks' существует
                # Save the block's HTML
                html_proc.save(block_html_content, block_html_file_path)
                logger.info(f"Saved block HTML: {block_html_file_path.relative_to(run_folder)}") # NEW: Log saving
                print(f"  Saved block HTML: {block_html_file_path.relative_to(run_folder)}")

            # Process and save JSON - ИСПРАВЛЕНО: сохраняем в подпапку page_name
            json_file_path = run_folder / page_name / f"{page_name}.json" # JSON в подпапку
            json_proc.save(scraped_data, json_file_path)
            logger.info(f"Saved JSON: {json_file_path.relative_to(run_folder)}") # NEW: Log saving
            print(f"  Saved Page HTML: {html_file_path.relative_to(run_folder)}, JSON: {json_file_path.relative_to(run_folder)}")

        except Exception as e:
            logger.error(f"Error processing page {page_name}: {e}", exc_info=True) # NEW: Log error with traceback
            print(f"  Error processing page {page_name}: {e}")
            # Optionally log error to a file within run_folder
            error_log_path = run_folder / "error_log.txt"
            with open(error_log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"Page {page_name}: {e}\n")
            continue # Skip to the next page

    print(f"\n--- Parsing completed for '{selected_subject_name}'. Data saved in: {run_folder} ---")
    logger.info(f"Parsing completed for '{selected_subject_name}'. Data saved in: {run_folder}") # NEW: Log completion

    # NEW: Keep the main thread alive to allow API servers to run
    try:
        print("Press Ctrl+C to stop the API servers and exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        logger.info("Shutdown signal received.")
        os._exit(0) # Exit the script when Ctrl+C is pressed

if __name__ == "__main__":
    main()
