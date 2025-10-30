"""Main entry point for the FIPI Parser application.
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
from api.core_api import create_core_app
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
    """
    problems_dir = Path("problems")
    if not problems_dir.exists():
        return {}

    subjects = {}
    for subject_dir in problems_dir.iterdir():
        if subject_dir.is_dir():
            db_path = subject_dir / "fipi_data.db"
            if db_path.exists():
                subjects[subject_dir.name] = subject_dir
    return subjects

def run_api_only(selected_subject_name, subject_base_folder):
    """Runs the API servers without scraping, loading dependencies from a specified subject folder.
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
            if e.errno == 98:  # Address already in use
                logger.error(f"Failed to start {name} server on {host}:{port}: Address already in use ({e.errno}).")
                print(f"ERROR: Cannot start {name} server on {host}:{port}. Address already in use. Please stop the other process using this port first.")
                os._exit(1)  # Exit the script if port is in use
            else:
                logger.error(f"Failed to start {name} server on {host}:{port}: {e}")
                print(f"ERROR: Cannot start {name} server on {host}:{port}. Reason: {e}")
                os._exit(1)  # Exit the script for any other error
        except Exception as e:
            logger.error(f"Unexpected error in {name} server thread: {e}", exc_info=True)
            print(f"ERROR: Unexpected error in {name} server thread: {e}")
            os._exit(1)  # Exit the script for any other error

    # Start API servers in background threads using the target function
    # Start Answer API on port 8000
    logger.info("Starting Answer API server in background thread...")
    answer_api_thread = threading.Thread(target=run_server, args=(answer_app, "127.0.0.1", 8000, "Answer API"))
    answer_api_thread.daemon = True
    answer_api_thread.start()
    # Brief wait to allow the thread to attempt startup and potentially log the error before proceeding
    time.sleep(1)
    logger.info("Answer API server startup process initiated in background thread.")

    # Start Core API on a different port, e.g., 8001
    logger.info("Starting Core API server in background thread...")
    core_api_thread = threading.Thread(target=run_server, args=(core_app, "127.0.0.1", 8001, "Core API"))
    core_api_thread.daemon = True
    core_api_thread.start()
    # Brief wait to allow the thread to attempt startup and potentially log the error before proceeding
    time.sleep(1)
    logger.info("Core API server startup process initiated in background thread.")

    print(f"✅ API servers started for '{selected_subject_name}' using data from: {subject_base_folder} -")
    print(f"- Web UI available at: https://ixem.duckdns.org -")
    logger.info(f"API servers started for '{selected_subject_name}' using data from: {subject_base_folder}")

    # Keep the main thread alive to allow API servers to run
    try:
        print("Press Ctrl+C to stop the API servers and exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        logger.info("Shutdown signal received.")
        os._exit(0)  # Exit the script when Ctrl+C is pressed


def main():
    """Main function to run the FIPI parser.

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
            print("\n🔍 Fetching available subjects from FIPI...")
            try:
                available_subjects = fipi_scraper.get_available_subjects(config.FIPI_SUBJECTS_URL)
                if not available_subjects:
                    print("❌ No subjects found or failed to fetch subjects from FIPI.")
                    continue # Go back to main menu
            except Exception as e:
                print(f"❌ Error fetching subjects: {e}")
                logger.error(f"Error fetching subjects: {e}", exc_info=True)
                continue # Go back to main menu

            print("\n📋 Available subjects:")
            for idx, (name, url) in enumerate(available_subjects.items(), start=1):
                print(f"{idx}. {name}")
            print(f"{len(available_subjects) + 1}. Back to Main Menu")

            while True:
                selection_input = input(f"\n🔢 Enter the number of the subject to scrape (or 'b' to go back): ").strip()
                if selection_input.lower() == 'b':
                    print("- Returning to Main Menu -")
                    break
                try:
                    selection = int(selection_input)
                    if 1 <= selection <= len(available_subjects):
                        selected_subject_name, selected_subject_url = list(available_subjects.items())[selection - 1]
                        subject_output_dir = Path("problems") / sanitize_subject_name(selected_subject_name)
                        db_path = subject_output_dir / "fipi_data.db"

                        # Check if data already exists for this subject
                        if db_path.exists():
                            print(f"\n⚠️  Data for '{selected_subject_name}' already exists at {subject_output_dir}.")
                            print("What would you like to do?")
                            print("1. Restart scraping (delete existing data)")
                            print("2. Continue scraping (may overwrite or skip)")
                            print("3. Cancel")

                            while True:
                                action_choice = input("Enter your choice (1/2/3): ").strip()
                                if action_choice == '1':
                                    # Delete existing data
                                    try:
                                        # Remove the database file
                                        db_path.unlink()
                                        # Remove other files in the directory if necessary
                                        json_files = glob.glob(str(subject_output_dir / "*.json"))
                                        html_files = glob.glob(str(subject_output_dir / "blocks" / "*" / "*.html")) # Example for nested blocks
                                        for file_path in json_files + html_files:
                                            Path(file_path).unlink()
                                        # Also remove the assets folder if it exists
                                        assets_dir = subject_output_dir / "assets"
                                        if assets_dir.exists() and assets_dir.is_dir():
                                            shutil.rmtree(assets_dir)
                                        print(f"✅ Deleted existing data in {subject_output_dir}")
                                    except Exception as e:
                                        logger.error(f"Error clearing existing data in {subject_output_dir}: {e}")
                                        print(f"Error clearing {e}. Proceeding, but issues might occur.")
                                    # Create the subject directory if it doesn't exist
                                    subject_output_dir.mkdir(parents=True, exist_ok=True)
                                    break # Exit action choice loop
                                elif action_choice == '2':
                                    print(f"✅ Continuing scraping for '{selected_subject_name}', potentially overwriting or skipping based on logic.")
                                    # No deletion, just proceed
                                    break # Exit action choice loop
                                elif action_choice == '3':
                                    print("Scraping cancelled by user.")
                                    break # Exit action choice loop
                                else:
                                    print("Invalid choice. Please enter 1, 2, or 3.")

                            if action_choice == '3':
                                continue # Go back to subject selection

                        else:
                            # Create the subject directory if it doesn't exist
                            subject_output_dir.mkdir(parents=True, exist_ok=True)
                            print(f"Created output directory: {subject_output_dir}")

                        # 1. Initialize Scraper
                        scraper = fipi_scraper.FIPIScraper(base_url=config.FIPI_QUESTIONS_URL, subjects_url=config.FIPI_SUBJECTS_URL)

                        # NEW: Allow override for total pages (for testing or specific subjects)
                        total_pages_override = config.TOTAL_PAGES # Use config value, or set to None to get from page 1

                        # NEW: Initialize DatabaseManager for this subject
                        logger.info("Initializing DatabaseManager for scraping")
                        db_manager = DatabaseManager(str(db_path))
                        db_manager.initialize_db()

                        # NEW: Initialize LocalStorage for this subject
                        storage_file = subject_output_dir / "answers.json"
                        logger.info("Initializing LocalStorage for scraping")
                        storage = LocalStorage(storage_file)

                        # NEW: Initialize AnswerChecker for this subject (likely not needed for scraping, but kept if needed later)
                        checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)

                        # 4. Initialize processors
                        html_proc = html_renderer.HTMLRenderer(db_manager=db_manager) # Use db_manager
                        json_proc = json_saver.JSONSaver()

                        # 5. Scrape and process pages
                        # Include 'init' page and pages 1 to total_pages
                        page_list = ["init"] + [str(i) for i in range(1, total_pages_override + 1)]
                        total_pages_to_process = len(page_list)

                        for idx, page_name in enumerate(page_list):
                            print(f"\n📄 Processing page: {page_name} ({idx + 1}/{total_pages_to_process}) for '{selected_subject_name}'")
                            try:
                                # Scrape the page
                                page_data = scraper.scrape_page(selected_subject_url, page_name)
                                if not page_data:
                                    print(f"  ❌ No data found on page {page_name}, skipping.")
                                    continue

                                # Process the data (save JSON, render HTML)
                                json_file_path = json_proc.save(page_data, subject_output_dir / f"{page_name}.json")
                                html_file_path = html_proc.save(html_proc.render(page_data, page_name), subject_output_dir / f"blocks/{page_name}.html")

                                # NEW: Save problems to database using DatabaseManager
                                problems = page_data.get("problems", [])
                                for problem in problems:
                                    db_manager.save_problem(problem)

                                logger.info(f"Saved HTML: {html_file_path.relative_to(subject_output_dir)}")
                                logger.info(f"Saved JSON: {json_file_path.relative_to(subject_output_dir)}")
                                print(f" ✅ Saved Page HTML: {html_file_path.relative_to(subject_output_dir)}, JSON: {json_file_path.relative_to(subject_output_dir)}")
                            except Exception as e:
                                logger.error(f"Error processing page {page_name}: {e}", exc_info=True)
                                print(f" ❌ Error processing page {page_name}: {e}")
                                error_log_path = subject_output_dir / "error_log.txt"
                                with open(error_log_path, 'a', encoding='utf-8') as log_file:
                                    log_file.write(f"Page {page_name}: {e}\n")
                                # Continue with other pages
                                print(f" ⚠️  Skipped page {page_name} due to error. Check error_log.txt.")

                        print(f"\n🎉 Parsing completed for '{selected_subject_name}'. Data saved in: {subject_output_dir} -")
                        logger.info(f"Parsing completed for '{selected_subject_name}'. Data saved in: {subject_output_dir}")

                    elif selection == len(available_subjects) + 1:
                        print("- Returning to Main Menu -")
                        break # Go back to main menu
                    else:
                        print("❌ Invalid number.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number or 'b'.")

            if selection_input.lower() != 'b':
                 print("- Returning to Main Menu -")
                 continue # Go back to main menu

        elif choice == '2':
            # Start API
            print("\n🌐 Starting API servers...")
            # Check for existing subjects (folders in problems/)
            existing_subjects = find_existing_subjects()
            has_existing_data = bool(existing_subjects)

            if has_existing_data:
                print(f"📂 Found existing data for subjects: {list(existing_subjects.keys())}")
                # Let user choose or use default
                print("Select a subject to serve via API:")
                subject_keys = list(existing_subjects.keys())
                for idx, subj_name in enumerate(subject_keys, start=1):
                    print(f"{idx}. {subj_name}")

                while True:
                    api_choice_input = input(f"🔢 Enter the number of the subject (or 'b' to go back): ").strip()
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
                     print("- Returning to Main Menu -")
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
