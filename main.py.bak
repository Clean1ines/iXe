"""
Main entry point for the FIPI Parser application.

This script orchestrates the scraping process of educational tasks (problems)
from the FIPI website. It provides an interactive command-line interface
to select subjects and initiate scraping. Data is saved in a structured
format (SQLite database and HTML files) to a designated directory.

The scraping is iterative: it starts from the 'init' page and then
proceeds through numbered pages (1, 2, ...) until a specified number
of consecutive empty pages is encountered.

Attributes:
    EXAM_YEAR (str): The target exam year for scraped data (currently hardcoded).
"""

import asyncio
import config
from scraper.fipi_scraper import FIPIScraper
from utils.database_manager import DatabaseManager
from utils.logging_config import setup_logging
from utils.browser_manager import BrowserManager
from utils.subject_mapping import get_alias_from_official_name, get_subject_key_from_alias
import logging
from pathlib import Path
import shutil

# === ГОД ЭКЗАМЕНА (можно вынести в config позже) ===
EXAM_YEAR = "2026"

def get_subject_output_dir(subject_name: str) -> Path:
    """
    Returns the output directory path for a given subject.

    Constructs the path as data/{alias}/{year}/ based on the subject name.
    Uses the mapping utility to get the alias.

    Args:
        subject_name (str): The official Russian name of the subject.

    Returns:
        Path: The pathlib.Path object representing the output directory.
    """
    alias = get_alias_from_official_name(subject_name)
    return Path("data") / alias / EXAM_YEAR

async def main():
    """
    The main asynchronous function providing the CLI loop for scraping.

    It initializes logging, displays a menu, fetches available subjects
    from FIPI using BrowserManager's dedicated subjects list page,
    allows the user to select a subject, handles existing data (prompting for restart),
    creates the output directory, initializes the database, and then
    iteratively scrapes pages for the selected subject using BrowserManager.
    """
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)
    logger.info("FIPI Parser Started (Scraping Mode)")

    print("🚀 Welcome to the FIPI Parser!")
    print("📋 1. Scrape a new subject or update existing data")
    print("🚪 2. Exit")
    print("-" * 40)

    while True:
        choice = input("👉 Enter your choice (1/2): ").strip()

        if choice == '1':
            print("\n🔍 Fetching available subjects from FIPI...")
            try:
                # --- ИНТЕГРАЦИЯ BROWSERMANAGER ---
                async with BrowserManager() as browser_manager:
                    # Get the dedicated page for the subjects list
                    subjects_list_page = await browser_manager.get_subjects_list_page()

                    scraper = FIPIScraper(
                        base_url=config.FIPI_QUESTIONS_URL, # This is likely the base for questions.php
                        browser_manager=browser_manager, # PASS BROWSER MANAGER
                        subjects_url=config.FIPI_SUBJECTS_URL # This should be /bank/ or derived from base_url
                    )
                    # Pass the dedicated subjects list page to get_projects
                    projects = await scraper.get_projects(subjects_list_page)
                    # --- /ИНТЕГРАЦИЯ BROWSERMANAGER ---
                if not projects:
                    print("❌ No subjects found.")
                    continue
            except Exception as e:
                print(f"❌ Error fetching subjects: {e}")
                logger.error(f"Error fetching subjects: {e}", exc_info=True)
                continue

            project_list = list(projects.items())
            print("\n📋 Available subjects:")
            for idx, (proj_id, name) in enumerate(project_list, start=1):
                print(f"{idx}. {name}")
            print(f"{len(project_list) + 1}. Back to Main Menu")

            while True:
                selection_input = input(f"\n🔢 Enter the number of the subject to scrape (or 'b' to go back): ").strip()
                if selection_input.lower() == 'b':
                    break

                try:
                    selection = int(selection_input)
                    if 1 <= selection <= len(project_list):
                        proj_id, subject_name = project_list[selection - 1]
                        subject_dir = get_subject_output_dir(subject_name)
                        db_path = subject_dir / "fipi_data.db"

                        if db_path.exists():
                            print(f"\n⚠️  Data for '{subject_name}' already exists at {subject_dir}.")
                            print("1. Restart scraping (delete existing data)")
                            print("2. Cancel")
                            action = input("Enter choice (1/2): ").strip()
                            if action == '1':
                                shutil.rmtree(subject_dir, ignore_errors=True)
                                print(f"✅ Deleted existing data in {subject_dir}")
                            else:
                                print("Scraping cancelled.")
                                continue

                        subject_dir.mkdir(parents=True, exist_ok=True)
                        db_manager = DatabaseManager(str(db_path))
                        db_manager.initialize_db()
                        print(f"📁 Output directory: {subject_dir}")

                        # === ИТЕРАТИВНЫЙ СКРАПИНГ ===
                        print("📄 Scraping pages iteratively until empty...")
                        total_saved = 0

                        # Determine the subject key for scraping based on the selected subject_name
                        alias = get_alias_from_official_name(subject_name)
                        scraping_subject_key = get_subject_key_from_alias(alias)

                        # Скрапим страницу "init"
                        try:
                            # --- ИНТЕГРАЦИЯ BROWSERMANAGER ---
                            problems, _ = await scraper.scrape_page(
                                proj_id=proj_id,
                                page_num="init",
                                run_folder=subject_dir,
                                subject=scraping_subject_key # PASS SUBJECT KEY
                            )
                            # --- /ИНТЕГРАЦИЯ BROWSERMANAGER ---
                            if problems:
                                for problem in problems:
                                    if not getattr(problem, 'subject', None):
                                        problem.subject = scraping_subject_key
                                db_manager.save_problems(problems)
                                total_saved += len(problems)
                                print(f" ✅ Saved {len(problems)} problems from page init")
                            else:
                                print(" ⚠️  Page init is empty")
                        except Exception as e:
                            print(f" ❌ Error on page init: {e}")
                            logger.error(f"Error scraping page init: {e}", exc_info=True)

                        # Скрапим страницы 1, 2, 3, ...
                        page_num = 1
                        empty_count = 0
                        max_empty = 2

                        while empty_count < max_empty:
                            print(f"📄 Trying page {page_num} ...")
                            try:
                                # --- ИНТЕГРАЦИЯ BROWSERMANAGER ---
                                problems, _ = await scraper.scrape_page(
                                    proj_id=proj_id,
                                    page_num=str(page_num),
                                    run_folder=subject_dir,
                                    subject=scraping_subject_key # PASS SUBJECT KEY
                                )
                                # --- /ИНТЕГРАЦИЯ BROWSERMANAGER ---
                                if len(problems) == 0:
                                    empty_count += 1
                                    print(f"   ⚠️  Page {page_num} is empty ({empty_count}/{max_empty})")
                                else:
                                    empty_count = 0
                                    for problem in problems:
                                        if not getattr(problem, 'subject', None):
                                            problem.subject = scraping_subject_key
                                    db_manager.save_problems(problems)
                                    total_saved += len(problems)
                                    print(f"   ✅ Saved {len(problems)} problems from page {page_num}")
                            except Exception as e:
                                print(f"   ❌ Error on page {page_num}: {e}")
                                logger.error(f"Error scraping page {page_num}: {e}", exc_info=True)
                                empty_count += 1
                            page_num += 1

                        print(f"\n🎉 Scraping completed! Total problems saved: {total_saved}")
                        logger.info(f"Scraping finished for '{subject_name}', {total_saved} problems saved.")

                    elif selection == len(project_list) + 1:
                        break
                    else:
                        print("❌ Invalid number.")
                except ValueError:
                    print("❌ Please enter a valid number.")

        elif choice == '2':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")


if __name__ == "__main__":
    asyncio.run(main())

