# main.py
"""
Main entry point for the FIPI Parser application.

This script orchestrates the scraping process:
1. Loads configuration.
2. Fetches available subjects from the FIPI website.
3. Provides a console interface for the user to select a subject.
4. Scrapes pages for the selected subject.
5. Processes and saves the data using dedicated modules.
"""

import config
from scraper import fipi_scraper
from processors import html_renderer, json_saver
from pathlib import Path
from datetime import datetime

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

    # 4. Initialize processors
    html_proc = html_renderer.HTMLRenderer()
    json_proc = json_saver.JSONSaver()

    # 5. Scrape and process pages
    page_list = ["init"] + [str(i) for i in range(1, config.TOTAL_PAGES + 1)]

    for page_name in page_list:
        print(f"Processing page: {page_name} for subject '{selected_subject_name}'...")
        try:
            # Scrape raw data for the page - ИСПРАВЛЕНО: передаем run_folder
            scraped_data = scraper.scrape_page(selected_proj_id, page_name, run_folder)

            if not scraped_data:
                print(f"  Warning: No data scraped for page {page_name}. Skipping.")
                continue

            # --- Process and save HTML for the entire PAGE (as before) ---
            html_content = html_proc.render(scraped_data)
            html_file_path = run_folder / page_name / f"{page_name}.html" # HTML в подпапку
            html_file_path.parent.mkdir(parents=True, exist_ok=True) # Убедиться, что подпапка существует
            html_proc.save(html_content, html_file_path)

            # --- Process and save HTML for EACH BLOCK separately ---
            # ИСПРАВЛЕНО: Добавляем цикл по blocks_html
            blocks_html = scraped_data.get("blocks_html", [])
            for block_idx, block_content in enumerate(blocks_html):
                # Generate HTML for a single block using the new method
                # ИСПРАВЛЕНО: Передаём asset_path_prefix="../assets" для коррекции путей
                block_html_content = html_proc.render_block(block_content, block_idx, asset_path_prefix="../assets") # Используем новый метод с префиксом
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


if __name__ == "__main__":
    main()