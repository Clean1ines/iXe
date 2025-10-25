# processors/html_renderer.py
"""
Module for rendering scraped data into HTML format.

This module provides the `HTMLRenderer` class which takes processed data
from the scraper and generates a complete HTML document using Jinja2 templates.
It now delegates UI component rendering to `ui_components.py`.
"""

import json
import logging
import re
from typing import Dict, Any, Optional

# NEW: Import DatabaseManager
from utils.database_manager import DatabaseManager
from . import ui_components  # Импортируем модуль с компонентами
# NEW: Import Jinja2 components
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

logger = logging.getLogger(__name__)


class HTMLRenderer:
    """
    A class to render assignment data into an HTML string using Jinja2 templates.

    This class takes the dictionary of data produced by the scraper,
    prepares context data, and renders it using Jinja2 templates to generate
    complete HTML documents containing assignments, MathJax, and interactive forms.
    """

    # CHANGED: Constructor now accepts a DatabaseManager instance
    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the HTMLRenderer.

        Args:
            db_manager (DatabaseManager): Instance of the database manager
                                          to fetch initial state.
        """
        # Pre-compile the CSS cleaning regex for efficiency if used multiple times
        self._css_clean_pattern = re.compile(r'[^\{\}]+\{\s*\}')
        self._answer_form_renderer = ui_components.AnswerFormRenderer()
        self._db_manager = db_manager  # NEW: Store the database manager instance
        logger.debug("HTMLRenderer initialized with DatabaseManager instance.")

        # --- Jinja2 Setup for HTMLRenderer ---
        self._templates_dir = Path(__file__).parent.parent / "templates" / "ui_components"
        self._jinja_env = Environment(
            loader=FileSystemLoader(self._templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        logger.debug(f"Jinja2 Environment for HTMLRenderer initialized with template directory: {self._templates_dir}")
        # --------------------------------------

    def render(self, data: Dict[str, Any], page_name: str) -> str:
        """
        Renders the provided data dictionary into an HTML string for the entire page
        using the 'full_page.html.j2' template.

        Args:
            data (Dict[str, Any]): The data dictionary from the scraper.
                                   Expected keys: 'page_name', 'blocks_html', 'task_metadata'.
            page_name (str): The name of the current page, used for initial state loading.

        Returns:
            str: The complete HTML string for the page.
        """
        try:
            logger.info(f"Rendering HTML page for page_name: {page_name}, blocks_html count: {len(data.get('blocks_html', []))}, task_metadata count: {len(data.get('task_metadata', []))}")
            # CHANGED: Load initial state from DatabaseManager instead of LocalStorage
            # NEW: Get task_ids from metadata to fetch specific answers
            task_metadata = data.get("task_metadata", [])
            task_ids = [metadata.get('task_id', '') for metadata in task_metadata if metadata.get('task_id')]
            # NEW: Fetch answers and statuses for the specific task IDs on this page
            # Assuming DatabaseManager has a method get_answers_for_task_ids
            # If not, implement it or adapt the call to existing methods like get_answer_and_status for each ID
            logger.debug(f"Fetching initial state for {len(task_ids)} task IDs for page {page_name}. Task IDs: {task_ids[:5]}...")
            initial_state = self._get_filtered_initial_state_from_db(task_ids)
            logger.debug(f"Retrieved initial state for {len(initial_state)} tasks for page {page_name}.")

            blocks_html = data.get("blocks_html", [])
            # task_metadata is already used above

            # Prepare data for the template
            page_data = {"page_name": page_name, "subject_name": "ЕГЭ"} # Assuming a default or parsing page_name for subject
            initial_state_json = json.dumps(initial_state, ensure_ascii=False, indent=2)
            initial_state_js = f"<script>\nvar INITIAL_PAGE_STATE = {initial_state_json};\n</script>\n"

            # Process each block to create the required structure for the template
            task_blocks_data = []
            for idx, block_html in enumerate(blocks_html):
                # Get metadata for the current block
                metadata = task_metadata[idx] if idx < len(task_metadata) else {}
                task_id = metadata.get('task_id', '')
                form_id = metadata.get('form_id', '')

                # Render the answer form for this block
                form_html = self._answer_form_renderer.render(idx)
                # Create the wrapper HTML for the block
                block_wrapper_html = f"<div class='processed_qblock' id='processed_qblock_{idx}' data-task-id='{task_id}' data-form-id='{form_id}'>{block_html}\n{form_html}\n</div>\n<hr>\n"
                task_blocks_data.append({"index": idx, "html": block_wrapper_html})

            # Prepare the context for the Jinja2 template
            template_context = {
                "page_data": page_data,
                "task_blocks": task_blocks_data,
                "initial_state_js": initial_state_js,
                "common_css": ui_components.COMMON_CSS,
                "common_js_functions": ui_components.COMMON_JS_FUNCTIONS,
                "lang": "ru"
            }

            # Render the template
            template = self._jinja_env.get_template("full_page.html.j2")
            result_html = template.render(template_context)

            logger.info(f"Successfully rendered HTML for page {page_name}, length: {len(result_html)} characters.")
            return result_html
        except Exception as e:
            logger.error(f"Error rendering HTML for page {page_name}: {e}", exc_info=True)
            raise

    def render_block(self, block_html: str, block_index: int, asset_path_prefix: Optional[str] = None, task_id: Optional[str] = "", form_id: Optional[str] = "", page_name: Optional[str] = None) -> str:
        """
        Renders a single assignment block HTML string using the 'single_block_page.html.j2' template.

        Args:
            block_html (str): The raw HTML content of the assignment block.
            block_index (int): The index of the block for form/ID generation.
            asset_path_prefix (Optional[str]): A prefix to adjust relative paths for assets like images.
                                               If provided (e.g., "../assets"), paths in block_html like
                                               "assets/image.jpg" will be changed to "{prefix}/image.jpg".
            task_id (Optional[str]): The task ID to embed in the block.
            form_id (Optional[str]): The form ID to embed in the block.
            page_name (Optional[str]): The name of the current page, used for initial state loading for the block.

        Returns:
            str: The complete HTML string for the single block, including MathJax and form.
        """
        try:
            logger.info(f"Rendering HTML block for block_index: {block_index}, task_id: {task_id}, page_name: {page_name}")
            # CHANGED: Load initial state for a specific block from DatabaseManager
            # NEW: Use the provided task_id for this specific block
            initial_state = {}
            if task_id:
                # NEW: Fetch answer and status for the specific task_id
                # Assuming DatabaseManager has a method get_answer_and_status
                logger.debug(f"Fetching initial state for block {block_index} using task_id: {task_id}")
                user_answer, status = self._db_manager.get_answer_and_status(task_id=task_id)
                # NEW: Construct the initial state object for this single task
                if user_answer is not None or status != "not_checked": # Only include if there's data
                    initial_state = {task_id: {"answer": user_answer, "status": status}}
                    logger.debug(f"Retrieved initial state for block {block_index} (task_id {task_id}): {initial_state}")


            # Use the common CSS and JS from ui_components
            # Adjust asset paths in block_html if prefix is provided
            processed_block_html = block_html
            if asset_path_prefix:
                # Example regex for <img src="..."> and <a href="...">
                # This is a basic example, might need refinement for other tags/attributes
                # FIXED: The regex now carefully captures only the src or href attribute
                # It looks for src="assets/..." or href="assets/..." (or with single quotes)
                # (\1) - captures src=" or href=" or src=' or href='
                # assets/ - the prefix to find
                # (\2) - captures the rest of the path
                # (\3) - captures the closing quote
                pattern = r'((src|href)\s*=\s*["\'])assets/([^"\']*)(["\'])'

                def replace_path(match):
                    prefix = asset_path_prefix
                    if not prefix.endswith('/'):
                        prefix += '/'
                    # match.group(1) = "src=" or "href=" (with quote)
                    # match.group(3) = the rest of the path
                    # match.group(4) = closing quote
                    return f"{match.group(1)}{prefix}{match.group(3)}{match.group(4)}"

                processed_block_html = re.sub(pattern, replace_path, block_html)

            # Prepare data for the template
            initial_state_json = json.dumps(initial_state, ensure_ascii=False, indent=2)
            initial_state_js = f"<script>\nvar INITIAL_PAGE_STATE = {initial_state_json};\n</script>\n"

            # Render the answer form for this block
            form_html = self._answer_form_renderer.render(block_index)
            # Create the wrapper HTML for the block
            wrapped_block_html = f"<div class='processed_qblock' id='processed_qblock_{block_index}' data-task-id='{task_id}' data-form-id='{form_id}'>{processed_block_html}\n{form_html}\n</div>"

            # Prepare the context for the Jinja2 template
            template_context = {
                "block_data": {
                    "block_index": block_index,
                    "task_id": task_id,
                    "html": wrapped_block_html
                },
                "initial_state_js": initial_state_js,
                "common_css": ui_components.COMMON_CSS,
                "common_js_functions": ui_components.COMMON_JS_FUNCTIONS,
                "lang": "ru"
            }

            # Render the template
            template = self._jinja_env.get_template("single_block_page.html.j2")
            result_html = template.render(template_context)

            logger.info(f"Successfully rendered HTML for block {block_index}, length: {len(result_html)} characters.")
            return result_html
        except Exception as e:
            logger.error(f"Error rendering HTML for block {block_index} (task_id {task_id}): {e}", exc_info=True)
            raise

    def save(self, html_string: str, path: str) -> None:
        """
        Saves the provided HTML string to a file.

        Args:
            html_string (str): The HTML content to save.
            path (str): The file path where the HTML should be saved.
        """
        try:
            logger.info(f"Saving HTML string to path: {path}, length: {len(html_string)} characters.")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html_string)
        except Exception as e:
            logger.error(f"Error saving HTML to path {path}: {e}", exc_info=True)
            raise

    def _clean_css(self, css_text: str) -> str:
        """
        Removes empty CSS rules from the provided CSS text.

        Args:
            css_text (str): The raw CSS string.

        Returns:
            str: The cleaned CSS string with empty rules removed.
        """
        return self._css_clean_pattern.sub('', css_text)

    # NEW: Helper method to fetch initial state for a list of task IDs
    def _get_filtered_initial_state_from_db(self, task_ids: list[str]) -> dict:
        """
        Fetches answers and statuses for a list of task IDs from the DatabaseManager.

        Args:
            task_ids (list[str]): List of task IDs to fetch data for.

        Returns:
            dict: A dictionary mapping task_id to {"answer": ..., "status": ...}.
        """
        logger.debug(f"Fetching initial state from DB for {len(task_ids)} task IDs: {task_ids[:5]}...")
        initial_state = {}
        for task_id in task_ids:
            if task_id: # Ensure task_id is not empty
                logger.debug(f"Fetching state for individual task_id: {task_id}")
                user_answer, status = self._db_manager.get_answer_and_status(task_id=task_id)
                logger.debug(f"Fetched state for {task_id}: answer present = {user_answer is not None}, status = {status}")
                # NEW: Only add to state if there's meaningful data
                if user_answer is not None or status != "not_checked":
                    initial_state[task_id] = {"answer": user_answer, "status": status}
        logger.debug(f"Aggregated initial state for {len(initial_state)} tasks out of {len(task_ids)} requested.")
        return initial_state

    # _get_js_functions and _get_answer_form_html are removed as their logic is now in ui_components
