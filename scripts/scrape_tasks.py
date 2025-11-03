"""
Script for scraping FIPI tasks and saving them to the database.

This script contains the main scraping logic that was previously in main.py.
It provides an interactive command-line interface to select subjects and
initiate scraping. Data is saved in a structured format (SQLite database
and HTML files) to a designated directory.

The scraping is iterative: it starts from the 'init' page and then
proceeds through numbered pages (1, 2, ...) until a specified number
of consecutive empty pages is encountered.
"""

import asyncio
import config
from scraper.fipi_scraper import FIPIScraper
from utils.database_manager import DatabaseManager
from utils.logging_config import setup_logging
from utils.browser_manager import BrowserManager
from utils.subject_mapping import get_alias_from_official_name, get_subject_key_from_alias, get_proj_id_for_subject, get_official_name_from_alias
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

async def scrape_subject_logic(proj_id: str, subject_name: str, scraping_subject_key: str, subject_dir: Path, db_manager: DatabaseManager):
    """
    Performs the iterative scraping for a given subject.
    """
    logger = logging.getLogger(__name__)
    # --- ИНТЕГРАЦИЯ BROWSERMANAGER и FIPISCRAPER ---
    # Используем BrowserManager как контекстный менеджер ВНУТРИ этой функции
    async with BrowserManager() as browser_manager:
        scraper = FIPIScraper(
            base_url=config.FIPI_QUESTIONS_URL,
            browser_manager=browser_manager,
            subjects_url=config.FIPI_SUBJECTS_URL
        )
        # === ИТЕРАТИВНЫЙ СКРАПИНГ ===
        print("📄 Scraping pages iteratively until empty...")
        total_saved = 0

        # Скрапим страницу "init"
        try:
            logger.debug(f"Attempting to scrape page 'init' for proj_id '{proj_id}' and subject '{scraping_subject_key}'")
            # --- ИНТЕГРАЦИЯ BROWSERMANAGER ---
            problems, _ = await scraper.scrape_page(
                proj_id=proj_id,
                page_num="init",
                run_folder=subject_dir,
                subject=scraping_subject_key # PASS SUBJECT KEY
            )
            # --- /ИНТЕГРАЦИЯ BROWSERMANAGER ---
            logger.debug(f"Scraping page 'init' returned {len(problems)} problems.")
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
                logger.debug(f"Attempting to scrape page '{page_num}' for proj_id '{proj_id}' and subject '{scraping_subject_key}'")
                # --- ИНТЕГРАЦИЯ BROWSERMANAGER ---
                problems, _ = await scraper.scrape_page(
                    proj_id=proj_id,
                    page_num=str(page_num),
                    run_folder=subject_dir,
                    subject=scraping_subject_key # PASS SUBJECT KEY
                )
                # --- /ИНТЕГРАЦИЯ BROWSERMANAGER ---
                logger.debug(f"Scraping page '{page_num}' returned {len(problems)} problems.")
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


async def main():
    """
    The main asynchronous function providing the CLI loop for scraping.

    It initializes logging, displays a menu, fetches available subjects
    from FIPI using BrowserManager's dedicated subjects list page,
    allows the user to select a subject, handles existing data (prompting for restart),
    creates the output directory, initializes the database, and then
    iteratively scrapes pages for the selected subject using BrowserManager.
    """
    # Установим уровень DEBUG для более подробного логирования
    setup_logging(level="DEBUG")
    logger = logging.getLogger(__name__)
    logger.info("FIPI Parser Started (Scraping Mode)")

    print("🚀 Welcome to the FIPI Parser!")
    print("📋 1. Scrape a new subject or update existing data")
    print("🚪 2. Exit")
    print("-" * 40)

    # Define available subjects directly based on subject_mapping
    # This avoids relying on the dynamic subjects list page which get_projects cannot parse.
    available_subjects = {
        "math": "Математика. Профильный уровень",
        "informatics": "Информатика и ИКТ",
        "rus": "Русский язык"
    }

    while True:
        choice = input("👉 Enter your choice (1/2): ").strip()

        if choice == '1':
            print("\n📋 Available subjects (hardcoded mapping):")
            subject_keys = list(available_subjects.keys())
            for idx, key in enumerate(subject_keys, start=1):
                print(f"{idx}. {key} ({available_subjects[key]})")
            print(f"{len(subject_keys) + 1}. Back to Main Menu")

            while True:
                selection_input = input(f"\n🔢 Enter the number of the subject to scrape (or 'b' to go back): ").strip()
                if selection_input.lower() == 'b':
                    break

                try:
                    selection = int(selection_input)
                    if 1 <= selection <= len(subject_keys):
                        selected_key = subject_keys[selection - 1]
                        subject_name = available_subjects[selected_key]
                        subject_dir = get_subject_output_dir(subject_name)
                        db_path = subject_dir / "fipi_data.db"

                        # Get proj_id using the mapping utility
                        try:
                            proj_id = get_proj_id_for_subject(selected_key)
                            logger.info(f"Mapped subject key '{selected_key}' to proj_id '{proj_id}'")
                        except KeyError as e:
                            print(f"❌ Error: Subject key '{selected_key}' not found in mappings: {e}")
                            logger.error(f"Subject key '{selected_key}' not found in mappings: {e}")
                            continue

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

                        # Determine the subject key for scraping based on the selected subject_name
                        alias = get_alias_from_official_name(subject_name)
                        scraping_subject_key = get_subject_key_from_alias(alias)

                        # Вызов функции, которая содержит цикл скрапинга внутри контекстного менеджера BrowserManager
                        await scrape_subject_logic(proj_id, subject_name, scraping_subject_key, subject_dir, db_manager)


                    elif selection == len(subject_keys) + 1:
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
