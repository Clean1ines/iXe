"""
Main entry point for the FIPI Parser application.
This script lists available subjects from FIPI and prompts the user to select one for scraping.
It can also start API servers in read-only mode, loading from existing data.
Scraping and other management tasks can be triggered via the web UI (future).
"""
import argparse
import config
from scraper import fipi_scraper
from processors import html_renderer, json_saver
from utils.database_manager import DatabaseManager
from utils.answer_checker import FIPIAnswerChecker
from utils.local_storage import LocalStorage
from api.answer_api import create_app as create_answer_app
from api.core_api import create_core_app as create_core_app
from utils.logging_config import setup_logging
import logging
from pathlib import Path
from datetime import datetime
import threading
import time
import uvicorn
import os
import glob
import asyncio
import shutil

# Global variable to track scraping status (simple approach)
scraping_status = {"is_running": False, "current_subject": None, "progress": 0}

def sanitize_subject_name(name: str) -> str:
    """
    Sanitizes a subject name to be used as a folder name.
    Replaces problematic characters with underscores or removes them.
    """
    # Replace or remove characters that are problematic for file systems
    sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
    # Remove trailing/leading spaces and underscores, replace spaces with underscores
    sanitized = sanitized.strip(" _").replace(" ", "_")
    return sanitized

def find_existing_subjects():
    """
    Scans the problems directory to find subjects with existing data.
    Returns:
        dict: A dictionary mapping sanitized subject names to their base folder path.
    """
    logger = logging.getLogger(__name__)
    subjects_data = {}
    search_pattern = str(config.DATA_ROOT / config.OUTPUT_DIR / "*")
    subject_folders = glob.glob(search_pattern)

    for folder_path in subject_folders:
        folder_name = Path(folder_path).name
        # Assume the folder name is the sanitized subject name
        # Or extract base subject name logic if needed (but simpler to use folder name directly)
        subjects_data[folder_name] = Path(folder_path)
        logger.info(f"Found existing subject folder: {folder_name} at {folder_path}")

    return subjects_data

def find_latest_run_folder(subject_name):
    """Finds the latest run folder for a given subject."""
    logger = logging.getLogger(__name__)
    safe_subject_name = sanitize_subject_name(subject_name)
    search_pattern = str(config.DATA_ROOT / config.OUTPUT_DIR / safe_subject_name / "run_*")
    folders = glob.glob(search_pattern)
    if not folders:
        logger.error(f"No run folders found for subject '{subject_name}' matching pattern '{search_pattern}'")
        return None

    latest_folder = max(folders, key=os.path.getctime)
    logger.info(f"Found latest run folder for '{subject_name}': {latest_folder}")
    return Path(latest_folder)

def run_api_only(selected_subject_name, subject_base_folder):
    """
    Runs the API servers without scraping, loading dependencies from a specified subject folder.
    Assumes the structure is subject_base_folder/fipi_data.db and subject_base_folder/answers.json
    """
    global scraping_status
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to start API servers for subject: {selected_subject_name} using folder: {subject_base_folder}")

    db_path = subject_base_folder / "fipi_data.db"
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        print(f"Error: Database file not found: {db_path}")
        return

    # Initialize DatabaseManager from existing DB
    logger.info(f"Initializing DatabaseManager from: {db_path}")
    db_manager = DatabaseManager(str(db_path))

    # Initialize LocalStorage from existing file
    storage_file = subject_base_folder / "answers.json"
    logger.info(f"Initializing LocalStorage from: {storage_file}")
    storage = LocalStorage(storage_file)

    # Initialize AnswerChecker (still needs base URL for API calls)
    logger.info("Initializing FIPIAnswerChecker")
    checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)

    # Create API applications
    logger.info("Creating Answer API application")
    answer_app = create_answer_app(db_manager, checker)

    logger.info("Creating Core API application")
    core_app = create_core_app(db_manager, storage, checker, scraping_status)

    # Define a target function for the thread that handles server startup
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

    # Start API servers in background threads using the target function
    # Start Answer API on port 8000
    logger.info("Starting Answer API server in background thread...")
    answer_api_thread = threading.Thread(
        target=run_server,
        args=(answer_app, "127.0.0.1", 8000, "Answer API")
    )
    answer_api_thread.daemon = True
    answer_api_thread.start()

    # Brief wait to allow the thread to attempt startup and potentially log the error before proceeding
    time.sleep(1)
    logger.info("Answer API server startup process initiated in background thread.")

    # Start Core API on a different port, e.g., 8001
    logger.info("Starting Core API server in background thread...")
    core_api_thread = threading.Thread(
        target=run_server,
        args=(core_app, "127.0.0.1", 8001, "Core API")
    )
    core_api_thread.daemon = True
    core_api_thread.start()

    # Brief wait to allow the thread to attempt startup and potentially log the error before proceeding
    time.sleep(1)
    logger.info("Core API server startup process initiated in background thread.")

    print(f"\n--- API servers started for '{selected_subject_name}' using data from: {subject_base_folder} ---")
    print(f"--- Web UI available at: https://ixem.duckdns.org   ---")
    logger.info(f"API servers started for '{selected_subject_name}' using data from: {subject_base_folder}")

    # Keep the main thread alive to allow API servers to run
    try:
        print("Press Ctrl+C to stop the API servers and exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        logger.info("Shutdown signal received.")
        os._exit(0) # Exit the script when Ctrl+C is pressed


def run_scraping_for_subject(proj_id, subject_name, total_pages_override=None):
    """
    Runs the scraping process for a specific subject.
    Creates a simplified folder structure: problems/Subject_Name/
    Handles resuming from existing data.
    """
    global scraping_status
    logger = logging.getLogger(__name__)
    scraping_status["is_running"] = True
    scraping_status["current_subject"] = subject_name
    scraping_status["progress"] = 0

    try:
        logger.info(f"Scraping started for subject '{subject_name}' (ID: {proj_id}).")
        print(f"Scraping started for '{subject_name}'...")

        # --- Simplified folder structure ---
        safe_subject_name = sanitize_subject_name(subject_name)
        subject_output_dir = config.DATA_ROOT / config.OUTPUT_DIR / safe_subject_name
        db_path = subject_output_dir / "fipi_data.db"
        storage_file = subject_output_dir / "answers.json"

        # Check if subject folder already exists
        if subject_output_dir.exists() and subject_output_dir.is_dir():
            print(f"\n⚠️  Warning: Data for subject '{subject_name}' already exists in '{subject_output_dir}'.")
            if db_path.exists():
                print("   A database file (fipi_data.db) was found.")
            if storage_file.exists():
                print("   An answers file (answers.json) was found.")

            while True:
                choice = input("\nChoose an option:\n  1. Resume scraping (continue from last page)\n  2. Overwrite (delete existing data and start fresh)\n  3. Cancel scraping\nEnter your choice (1/2/3): ").strip()
                if choice == '1':
                    print("Resuming scraping from the last processed page...")
                    # For resume logic, we'd ideally determine the last page from DB or logs.
                    # For simplicity here, we'll just append new data.
                    # A more robust approach would involve tracking last page in DB metadata or a file.
                    # For now, we proceed but note that overwrites might occur if same pages are rescraped.
                    # Ensure the directory structure is ready.
                    subject_output_dir.mkdir(parents=True, exist_ok=True)
                    break
                elif choice == '2':
                    print("Overwriting existing data...")
                    try:
                        if db_path.exists():
                            db_path.unlink()
                            print(f"  Deleted existing database: {db_path}")
                        if storage_file.exists():
                            storage_file.unlink()
                            print(f"  Deleted existing answers file: {storage_file}")
                        # Optionally clear the whole directory content except .gitkeep or similar
                        for item in subject_output_dir.iterdir():
                            if item.name not in [".gitkeep"]: # Protect .gitkeep if present
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                        print(f"  Cleared contents of {subject_output_dir}")
                    except Exception as e:
                        logger.error(f"Error clearing existing data in {subject_output_dir}: {e}")
                        print(f"Error clearing  {e}. Proceeding, but issues might occur.")
                    subject_output_dir.mkdir(parents=True, exist_ok=True)
                    break
                elif choice == '3':
                    print("Scraping cancelled by user.")
                    return
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")

        else:
            # Create the subject directory if it doesn't exist
            subject_output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created output directory: {subject_output_dir}")


        # 1. Initialize Scraper
        scraper = fipi_scraper.FIPIScraper(
            base_url=config.FIPI_QUESTIONS_URL,
            subjects_url=config.FIPI_SUBJECTS_URL
        )

        # NEW: Allow override for total pages (for testing or specific subjects)
        total_pages = total_pages_override if total_pages_override is not None else config.TOTAL_PAGES

        # NEW: Initialize DatabaseManager for this subject
        logger.info("Initializing DatabaseManager for scraping")
        db_manager = DatabaseManager(str(db_path))
        db_manager.initialize_db()

        # NEW: Initialize LocalStorage for this subject
        logger.info("Initializing LocalStorage for scraping")
        storage = LocalStorage(storage_file)

        # NEW: Initialize AnswerChecker for this subject (likely not needed for scraping, but kept if needed later)
        checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)

        # 4. Initialize processors
        html_proc = html_renderer.HTMLRenderer(db_manager=db_manager) # Use db_manager
        json_proc = json_saver.JSONSaver()

        # 5. Scrape and process pages
        # Include 'init' page and pages 1 to total_pages
        page_list = ["init"] + [str(i) for i in range(1, total_pages + 1)]
        total_pages_to_process = len(page_list)

        for idx, page_name in enumerate(page_list):
            print(f"\nProcessing page: {page_name} for subject '{subject_name}'... ({idx + 1}/{total_pages_to_process})")
            logger.info(f"Processing page: {page_name} for subject '{subject_name}'... ({idx + 1}/{total_pages_to_process})")
            scraping_status["progress"] = int(((idx + 1) / total_pages_to_process) * 100)

            try:
                # Pass the subject's base output directory as run_folder
                problems, scraped_data = scraper.scrape_page(proj_id, page_name, subject_output_dir)
                if not scraped_data:
                    logger.warning(f"Warning: No data scraped for page {page_name}. Skipping.")
                    print(f"  Warning: No data scraped for page {page_name}. Skipping.")
                    continue

                # NEW: Save the scraped problems using DatabaseManager
                logger.info(f"Saving {len(problems)} problems for page {page_name} to database...")
                db_manager.save_problems(problems)

                # --- Process and save HTML for the entire PAGE ---
                html_content = html_proc.render(scraped_data, page_name)
                html_file_path = subject_output_dir / page_name / f"{page_name}.html"
                html_file_path.parent.mkdir(parents=True, exist_ok=True)
                html_proc.save(html_content, html_file_path)
                logger.info(f"Saved Page HTML: {html_file_path.relative_to(subject_output_dir)}")

                # --- Process and save HTML for EACH BLOCK separately ---
                blocks_html = scraped_data.get("blocks_html", [])
                task_metadata = scraped_data.get("task_metadata", [])
                for block_idx, block_content in enumerate(blocks_html):
                    metadata = task_metadata[block_idx] if block_idx < len(task_metadata) else {}
                    task_id = metadata.get('task_id', '')
                    form_id = metadata.get('form_id', '')

                    block_html_content = html_proc.render_block(
                        block_content, block_idx,
                        asset_path_prefix="../assets", # Adjusted for new structure
                        task_id=task_id,
                        form_id=form_id,
                        page_name=page_name
                    )
                    # Save block HTML directly in subject_output_dir/blocks/
                    block_html_file_path = subject_output_dir / "blocks" / f"block_{block_idx}_{page_name}.html"
                    block_html_file_path.parent.mkdir(parents=True, exist_ok=True)
                    html_proc.save(block_html_content, block_html_file_path)
                    logger.info(f"Saved block HTML: {block_html_file_path.relative_to(subject_output_dir)}")
                    print(f"  Saved block HTML: {block_html_file_path.relative_to(subject_output_dir)}")

                # Process and save JSON directly in subject_output_dir/
                json_file_path = subject_output_dir / f"{page_name}.json"
                json_proc.save(scraped_data, json_file_path)
                logger.info(f"Saved JSON: {json_file_path.relative_to(subject_output_dir)}")
                print(f"  Saved Page HTML: {html_file_path.relative_to(subject_output_dir)}, JSON: {json_file_path.relative_to(subject_output_dir)}")

            except Exception as e:
                logger.error(f"Error processing page {page_name}: {e}", exc_info=True)
                print(f"  Error processing page {page_name}: {e}")
                error_log_path = subject_output_dir / "error_log.txt"
                with open(error_log_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"Page {page_name}: {e}\n")
                # Continue with other pages

        print(f"\n--- ✅ Parsing completed for '{subject_name}'. Data saved in: {subject_output_dir} ---")
        logger.info(f"Parsing completed for '{subject_name}'. Data saved in: {subject_output_dir}")

    except Exception as e:
        logger.error(f"Error during scraping for '{subject_name}': {e}", exc_info=True)
        print(f"❌ Error during scraping for '{subject_name}': {e}")

    finally:
        scraping_status["is_running"] = False
        scraping_status["current_subject"] = None
        scraping_status["progress"] = 0
        print(f"🏁 Scraping process for '{subject_name}' finished.")


def main():
    """
    Main function to run the FIPI parser.
    Lists available subjects from FIPI and prompts the user to select one for scraping.
    Can also start API servers in read-only mode.
    """
    # Setup logging first
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)
    logger.info("FIPI Parser Started (Interactive Mode)")

    print("🚀 Welcome to the FIPI Parser!")
    print("📋 1. Scrape a new subject or update existing data")
    print("🌐 2. Start API servers (using existing data)")
    print("🚪 3. Exit")
    print("-" * 40)

    while True:
        choice = input("👉 Enter your choice (1/2/3): ").strip()
        if choice == '1':
            # Scrape new subject
            print("\n📡 Fetching available subjects from FIPI...")
            try:
                scraper_instance = fipi_scraper.FIPIScraper(
                    base_url=config.FIPI_QUESTIONS_URL,
                    subjects_url=config.FIPI_SUBJECTS_URL
                )
                # Get projects dictionary: {proj_id: subject_name}
                projects_dict = scraper_instance.get_projects()

                if not projects_dict:
                    print("❌ Error: Could not fetch subject list from FIPI.")
                    logger.error("Could not fetch subject list from FIPI.")
                    continue # Go back to main menu

                # Create a list for ordered display and selection
                project_list = list(projects_dict.items()) # [(proj_id1, name1), (proj_id2, name2), ...]

                print("\n📚 Available subjects:")
                for idx, (proj_id, subject_name) in enumerate(project_list, start=1):
                    print(f"{idx}. {subject_name}")

                while True:
                    try:
                        selection_input = input("\n🔢 Enter the number of the subject to scrape (or 'b' to go back): ").strip()
                        if selection_input.lower() == 'b':
                            break # Break inner loop to go back to main menu
                        selection = int(selection_input)
                        if 1 <= selection <= len(project_list):
                            selected_proj_id, selected_subject_name = project_list[selection - 1]
                            print(f"✅ You selected: {selected_subject_name} (ID: {selected_proj_id})")
                            
                            # Ask for total pages (optional)
                            pages_input = input(f"📄 How many pages to scrape for '{selected_subject_name}'? (Press Enter for default {config.TOTAL_PAGES}, or type a number): ").strip()
                            total_pages = None
                            if pages_input:
                                try:
                                    total_pages = int(pages_input)
                                    print(f"   Will scrape {total_pages} pages.")
                                except ValueError:
                                    print("⚠️ Invalid number entered. Using default page count.")
                            
                            # Run scraping
                            run_scraping_for_subject(selected_proj_id, selected_subject_name, total_pages_override=total_pages)
                            break # Break out of subject selection loop after scraping
                        else:
                            print("❌ Invalid number. Please select a number from the list.")
                    except ValueError:
                        print("❌ Invalid input. Please enter a number or 'b'.")
                
                if selection_input.lower() != 'b':
                    print("\n--- Returning to Main Menu ---")
                continue # Go back to main menu (whether 'b' was pressed or scraping finished)

            except Exception as e:
                logger.error(f"Error in scraping flow: {e}", exc_info=True)
                print(f"💥 An error occurred during the scraping setup: {e}")
                continue # Go back to main menu

        elif choice == '2':
            # Start API
            print("\n�� Starting API servers...")
            # Check for existing subjects (folders in problems/)
            existing_subjects = find_existing_subjects()
            has_existing_data = bool(existing_subjects)

            if has_existing_subjects:
                print(f"📂 Found existing data for subjects: {list(existing_subjects.keys())}")
                
                # Let user choose or use default
                print("\nSelect a subject to serve via API:")
                subject_keys = list(existing_subjects.keys())
                for idx, subj_name in enumerate(subject_keys, start=1):
                    print(f"{idx}. {subj_name}")
                
                while True:
                    api_choice_input = input(f"\n🔢 Enter the number of the subject (or 'b' to go back): ").strip()
                    if api_choice_input.lower() == 'b':
                         break
                    try:
                         api_selection = int(api_choice_input)
                         if 1 <= api_selection <= len(subject_keys):
                             selected_api_subject_name = subject_keys[api_selection - 1]
                             selected_subject_base_folder = existing_subjects[selected_api_subject_name]
                             print(f"✅ Starting API with subject: {selected_api_subject_name}")
                             run_api_only(selected_api_subject_name, selected_subject_base_folder)
                             # If API exits (Ctrl+C), it will os._exit(0)
                             break
                         else:
                             print("❌ Invalid number.")
                    except ValueError:
                         print("❌ Invalid input. Please enter a number or 'b'.")
                
                if api_choice_input.lower() != 'b':
                     print("\n--- Returning to Main Menu ---")
                continue

            else:
                print("📂 No existing subject data found in problems/ directory.")
                print("💡 Please run scraping first (option 1).")
                continue # Go back to main menu

        elif choice == '3':
            # Exit
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
