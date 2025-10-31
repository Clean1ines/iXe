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
    SUBJECT_ALIAS_MAP (dict): Maps official Russian subject names
                              to shorter Latin aliases for directory names.
    EXAM_YEAR (str): The target exam year for scraped data (currently hardcoded).
"""

import asyncio
import config
from scraper.fipi_scraper import FIPIScraper
from utils.database_manager import DatabaseManager
from utils.logging_config import setup_logging
import logging
from pathlib import Path
import shutil

# === МАППИНГ: Официальное название → короткий алиас ===
SUBJECT_ALIAS_MAP = {
    "Математика. Профильный уровень": "promath",
    "Математика. Базовый уровень": "basemath",
    "Информатика и ИКТ": "inf",
    "Русский язык": "rus",
    "Физика": "phys",
    "Химия": "chem",
    "Биология": "bio",
    "История": "hist",
    "Обществознание": "soc",
    "Литература": "lit",
    "География": "geo",
    "Английский язык": "eng",
    "Немецкий язык": "de",
    "Французский язык": "fr",
    "Испанский язык": "es",
    "Китайский язык": "zh",
}

# === ГОД ЭКЗАМЕНА (можно вынести в config позже) ===
EXAM_YEAR = "2026"

def get_subject_output_dir(subject_name: str) -> Path:
    """
    Returns the output directory path for a given subject.

    Constructs the path as data/{alias}/{year}/ based on the subject name.
    If the subject name is not found in the alias map, it creates an alias
    by sanitizing the name.

    Args:
        subject_name (str): The official Russian name of the subject.

    Returns:
        Path: The pathlib.Path object representing the output directory.
    """
    alias = SUBJECT_ALIAS_MAP.get(subject_name)
    if not alias:
        # Fallback: sanitize and use latinized version
        alias = "".join(c if c.isalnum() else "_" for c in subject_name.lower())
        alias = alias[:20]  # limit length
    return Path("data") / alias / EXAM_YEAR

async def main():
    """
    The main asynchronous function providing the CLI loop for scraping.

    It initializes logging, displays a menu, fetches available subjects
    from FIPI, allows the user to select a subject, handles existing data
    (prompting for restart), creates the output directory, initializes
    the database, and then iteratively scrapes pages for the selected subject.
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
                scraper = FIPIScraper(
                    base_url=config.FIPI_QUESTIONS_URL,
                    subjects_url=config.FIPI_SUBJECTS_URL
                )
                projects = await asyncio.to_thread(scraper.get_projects)
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

                        # Скрапим страницу "init"
                        try:
                            problems, _ = await asyncio.to_thread(
                                scraper.scrape_page,
                                proj_id=proj_id,
                                page_num="init",
                                run_folder=subject_dir
                            )
                            if problems:
                                for problem in problems:
                                    if not getattr(problem, 'subject', None):
                                        alias = SUBJECT_ALIAS_MAP.get(subject_name, "unknown")
                                        # Маппинг алиаса → subject key
                                        subject_key_map = {
                                            "promath": "math",
                                            "basemath": "math",
                                            "inf": "informatics",
                                            "rus": "russian",
                                            "phys": "physics",
                                            "chem": "chemistry",
                                            "bio": "biology",
                                            "hist": "history",
                                            "soc": "social",
                                            "lit": "literature",
                                            "geo": "geography",
                                            "eng": "english",
                                            "de": "german",
                                            "fr": "french",
                                            "es": "spanish",
                                            "zh": "chinese",
                                        }
                                        problem.subject = subject_key_map.get(alias, "unknown")
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
                                problems, _ = await asyncio.to_thread(
                                    scraper.scrape_page,
                                    proj_id=proj_id,
                                    page_num=str(page_num),
                                    run_folder=subject_dir
                                )
                                if len(problems) == 0:
                                    empty_count += 1
                                    print(f"   ⚠️  Page {page_num} is empty ({empty_count}/{max_empty})")
                                else:
                                    empty_count = 0
                                    for problem in problems:
                                        if not getattr(problem, 'subject', None):
                                            alias = SUBJECT_ALIAS_MAP.get(subject_name, "unknown")
                                            subject_key_map = {
                                                "promath": "math",
                                                "basemath": "math",
                                                "inf": "informatics",
                                                "rus": "russian",
                                                "phys": "physics",
                                                "chem": "chemistry",
                                                "bio": "biology",
                                                "hist": "history",
                                                "soc": "social",
                                                "lit": "literature",
                                                "geo": "geography",
                                                "eng": "english",
                                                "de": "german",
                                                "fr": "french",
                                                "es": "spanish",
                                                "zh": "chinese",
                                            }
                                            problem.subject = subject_key_map.get(alias, "unknown")
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
