"""
Script for scraping FIPI tasks and saving them to the database.

This script contains the main scraping logic that was previously in main.py.
It provides an interactive command-line interface to select subjects and
initiate scraping. Data is saved in a structured format (SQLite database
and HTML files) to a designated directory.

The scraping is iterative: it starts from the 'init' page and then
proceeds through numbered pages (1, 2, ...) until the last page is reached
or a specified number of consecutive empty pages is encountered.
"""

import asyncio
import config
from scraper.fipi_scraper import FIPIScraper
from utils.database_manager import DatabaseManager
from utils.logging_config import setup_logging
from utils.browser_manager import BrowserManager
from utils.subject_mapping import SUBJECT_ALIAS_MAP, SUBJECT_KEY_MAP, SUBJECT_TO_PROJ_ID_MAP, SUBJECT_TO_OFFICIAL_NAME_MAP, get_alias_from_official_name, get_subject_key_from_alias, get_proj_id_for_subject, get_official_name_from_alias
import logging
from pathlib import Path
import shutil
from typing import Optional, Dict, Any


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

class CLIScraper:
    """
    Class to encapsulate the CLI scraping logic.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

    def setup_logging(self):
        """Initialize logging."""
        setup_logging(level="DEBUG") # Use DEBUG for detailed output during scraping
        self.logger.info("CLI Scraper initialized.")

    def get_available_subjects(self) -> Dict[str, str]:
        """
        Get available subjects from subject_mapping, excluding those without PROJ_IDS.
        Returns a mapping of subject_key to official_name.
        """
        available = {}
        # Iterate through SUBJECT_KEY_MAP to get subject_key and alias
        for alias, subject_key in SUBJECT_KEY_MAP.items():
            # Check if this subject_key has a corresponding proj_id
            if subject_key in SUBJECT_TO_PROJ_ID_MAP:
                # Get the official name using the alias
                official_name = SUBJECT_TO_OFFICIAL_NAME_MAP.get(alias, alias) # Fallback to alias if official name not found
                available[subject_key] = official_name
        return available

    async def scrape_subject_logic(self, proj_id: str, subject_name: str, scraping_subject_key: str, subject_dir: Path, db_manager: DatabaseManager):
        """
        Performs the iterative scraping for a given subject.
        """
        # --- ИНТЕГРАЦИЯ BROWSERMANAGER и FIPISCRAPER ---
        # Используем BrowserManager как контекстный менеджер ВНУТРИ этой функции
        async with BrowserManager() as browser_manager:
            scraper = FIPIScraper(
                base_url=config.FIPI_QUESTIONS_URL,
                browser_manager=browser_manager,
                subjects_url=config.FIPI_SUBJECTS_URL
            )
            # === ИТЕРАТИВНЫЙ СКРАПИНГ ===
            print("📄 Scraping pages iteratively until last page or max empty pages reached...")
            total_saved = 0

            # Скрапим страницу "init"
            try:
                self.logger.debug(f"Attempting to scrape page 'init' for proj_id '{proj_id}' and subject '{scraping_subject_key}'")
                problems, scraped_data = await scraper.scrape_page(
                    proj_id=proj_id,
                    page_num="init",
                    run_folder=subject_dir,
                    subject=scraping_subject_key # PASS SUBJECT KEY
                )
                self.logger.debug(f"Scraping page 'init' returned {len(problems)} problems.")
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
                self.logger.error(f"Error scraping page init: {e}", exc_info=True)

            # --- НОВАЯ ЛОГИКА: Определение последней страницы ---
            last_page_num = None
            try:
                # Navigate to page 1 to get the pager information
                general_page_for_pager = await browser_manager.get_general_page()
                page_1_url = f"{config.FIPI_QUESTIONS_URL}?proj={proj_id}&page=1"
                await general_page_for_pager.goto(page_1_url, wait_until="networkidle", timeout=30000)
                await general_page_for_pager.wait_for_selector(".pager", timeout=10000)

                last_page_js_handle = await general_page_for_pager.evaluate_handle(
                    """() => {
                        const pager = document.querySelector('.pager');
                        if (!pager) return null;
                        const buttons = Array.from(pager.querySelectorAll('.button'));
                        if (buttons.length === 0) return null;
                        // Get the 'p' attribute of the last button
                        const lastButton = buttons[buttons.length - 1];
                        return lastButton.getAttribute('p');
                    }"""
                )
                last_page_text = await last_page_js_handle.json_value()
                if last_page_text and last_page_text.isdigit():
                    last_page_num = int(last_page_text)
                    self.logger.info(f"Determined last page number: {last_page_num}")
                else:
                    self.logger.warning(f"Could not determine last page number from pager, got: {last_page_text}. Falling back to max_empty logic.")
                    last_page_num = None
                await general_page_for_pager.close()
            except Exception as e:
                self.logger.warning(f"Could not determine last page number from pager: {e}. Falling back to max_empty logic.")
                last_page_num = None
            # --- /НОВАЯ ЛОГИКА ---

            # Скрапим страницы 1, 2, 3, ... до last_page_num или пока не будет max_empty пустых подряд
            page_num = 1
            empty_count = 0
            max_empty = 2 # Keep this as a fallback if last_page_num is not determined

            while True:
                # Check if we've reached the determined last page
                if last_page_num is not None and page_num > last_page_num:
                    self.logger.info(f"Reached determined last page ({last_page_num}). Stopping scraping.")
                    break

                # Check if we've hit the max_empty limit (fallback if last_page_num is unknown)
                if last_page_num is None and empty_count >= max_empty:
                    self.logger.info(f"Reached {max_empty} consecutive empty pages. Stopping scraping.")
                    break

                print(f"📄 Trying page {page_num} ...")
                try:
                    self.logger.debug(f"Attempting to scrape page '{page_num}' for proj_id '{proj_id}' and subject '{scraping_subject_key}'")
                    problems, _ = await scraper.scrape_page(
                        proj_id=proj_id,
                        page_num=str(page_num),
                        run_folder=subject_dir,
                        subject=scraping_subject_key # PASS SUBJECT KEY
                    )
                    self.logger.debug(f"Scraping page '{page_num}' returned {len(problems)} problems.")
                    if len(problems) == 0:
                        empty_count += 1
                        print(f"   ⚠️  Page {page_num} is empty ({empty_count}/{max_empty})")
                    else:
                        empty_count = 0 # Reset counter on non-empty page
                        for problem in problems:
                            if not getattr(problem, 'subject', None):
                                problem.subject = scraping_subject_key
                        db_manager.save_problems(problems)
                        total_saved += len(problems)
                        print(f"   ✅ Saved {len(problems)} problems from page {page_num}")
                except Exception as e:
                    print(f"   ❌ Error on page {page_num}: {e}")
                    self.logger.error(f"Error scraping page {page_num}: {e}", exc_info=True)
                    # Increment empty count on error as well, to prevent infinite loops on consistently failing pages
                    empty_count += 1
                page_num += 1

            print(f"\n🎉 Scraping completed! Total problems saved: {total_saved}")
            self.logger.info(f"Scraping finished for '{subject_name}', {total_saved} problems saved.")


    async def run(self):
        """
        The main asynchronous function providing the CLI loop for scraping.
        """
        self.logger.info("FIPI Parser Started (Scraping Mode)")

        print("🚀 Welcome to the FIPI Parser!")
        print("📋 1. Scrape a new subject or update existing data")
        print("🚪 2. Exit")
        print("-" * 40)

        # Define available subjects directly based on subject_mapping
        available_subjects = self.get_available_subjects()

        while True:
            choice = input("👉 Enter your choice (1/2): ").strip()

            if choice == '1':
                print("\n📋 Available subjects (from mapping):")
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
                                self.logger.info(f"Mapped subject key '{selected_key}' to proj_id '{proj_id}'")
                            except KeyError as e:
                                print(f"❌ Error: Subject key '{selected_key}' not found in mappings: {e}")
                                self.logger.error(f"Subject key '{selected_key}' not found in mappings: {e}")
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
                            await self.scrape_subject_logic(proj_id, subject_name, scraping_subject_key, subject_dir, db_manager)


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


async def main():
    scraper = CLIScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
