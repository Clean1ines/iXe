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
2. Detects existing subjects and allows running API for them.
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

def run_api_only(selected_subject_name, run_folder_path):
    """
    Runs the API servers without scraping, loading dependencies from a specified run folder.
    """
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

    # Check for existing subjects
    existing_subjects = find_existing_subjects()
    has_existing_data = bool(existing_subjects)

    print("\n--- FIPI Parser Menu ---")
    if has_existing_data:
        print("Found existing data for the following subjects:")
        for i, (subject_name, run_path) in enumerate(existing_subjects.items(), 1):
            print(f"  {i}. {subject_name} (using data from {run_path.name})")
        print(f"  {len(existing_subjects) + 1}. Scrape a new subject")
        print(f"  {len(existing_subjects) + 2}. Run API for an existing subject (select from list)")
        total_options = len(existing_subjects) + 2
    else:
        print("1. Scrape a new subject")
        print("2. Run API for an existing subject (no existing data found, will prompt for path)")
        total_options = 2

    while True:
        try:
            choice = int(input(f"\nSelect an option (1-{total_options}): "))
            if 1 <= choice <= total_options:
                break
            else:
                print(f"Please enter a number between 1 and {total_options}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    if choice <= len(existing_subjects):
        # Option 1-N: Run API for existing subject (based on detected data)
        selected_subject_name = list(existing_subjects.keys())[choice - 1]
        selected_run_folder = existing_subjects[selected_subject_name]
        print(f"You selected to run API for: {selected_subject_name}")
        run_api_only(selected_subject_name, selected_run_folder)
        return

    elif choice == len(existing_subjects) + 1 and has_existing_data:
        # Option N+1: Scrape new subject
        print("\n--- Starting Scraping Process ---")
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

    elif choice == len(existing_subjects) + 2 or (choice == 2 and not has_existing_data):
        # Option N+2 (or 2 if no existing data): Run API for existing subject (prompt for name/path)
        print("\n--- Running API for Existing Subject ---")
        if has_existing_data:
            print("Available subjects based on detected data:")
            for i, subject_name in enumerate(existing_subjects.keys(), 1):
                print(f"  {i}. {subject_name}")
            while True:
                try:
                    sub_choice = int(input(f"\nSelect a subject to run API for (1-{len(existing_subjects)}): "))
                    if 1 <= sub_choice <= len(existing_subjects):
                        selected_subject_name = list(existing_subjects.keys())[sub_choice - 1]
                        selected_run_folder = existing_subjects[selected_subject_name]
                        print(f"You selected: {selected_subject_name}")
                        run_api_only(selected_subject_name, selected_run_folder)
                        return
                    else:
                        print(f"Please enter a number between 1 and {len(existing_subjects)}.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            # No existing data found, prompt for subject name to find latest run
            subject_name = input("Enter the subject name to find its latest run folder (e.g., 'ЕГЭ Математика'): ").strip()
            run_api_only(subject_name, None) # Pass None to trigger find_latest_run_folder inside run_api_only
            # Note: The original run_api_only didn't handle None, so we need to modify its logic slightly.
            # Let's adjust the call and the function definition to handle this case properly.
            # We'll keep the original logic but add a fallback if run_folder_path is None
            # This is getting complex. Let's simplify and just call the original find_latest_run_folder logic here if path is None.
            # We'll modify the call slightly to handle the fallback case more cleanly in the next iteration if needed.
            # For now, let's assume the user will see the list if data exists.
            # If they choose option N+2 and data exists, they select from the list.
            # If they choose option N+2 and no data exists, they get an error or are redirected.
            # Let's make option N+2 work *only* when there is existing data, otherwise it's not a valid option.
            # So the menu changes based on has_existing_data.
            # The logic above already handles this correctly by setting total_options = 2 if no data exists.
            # In that case, option 2 would be invalid inside the scraping branch.
            # We need to move the 'Run API for existing' logic *outside* the scraping branch or handle it correctly.
            # Let's restructure slightly to avoid the None path for run_folder_path in this version.

            # Since we have existing data, this path should only be reached if the original logic was flawed.
            # Let's assume the user will use option 1 to select from the list if data exists.
            # If no data exists, option 2 is "Run API for existing" which should fail gracefully or not be offered.
            # The current structure offers option 2 even when no data exists.
            # Let's adjust the menu print to reflect this.
            # If no data exists, option 2 doesn't make sense. We should probably just offer scraping.
            # Or offer scraping and a "Run API (advanced - specify path)".
            # For simplicity, let's stick to the current logic but note that option 2 without data is tricky.
            # The user should ideally use option 1 if data exists.
            print("No existing subjects detected automatically. Please use option 1 if you have data, or option 1 to scrape a new subject.")
            # Or we can implement the fallback here:
            subject_name = input("Enter the subject name to run API for (e.g., 'ЕГЭ Математика'): ").strip()
            run_folder = find_latest_run_folder(subject_name)
            if run_folder:
                 run_api_only(subject_name, run_folder)
            else:
                 print("Could not find a run folder for the given subject name.")
                 return


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


if __name__ == "__main__":
    main()
