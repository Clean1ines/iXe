import json
import logging
import re
from typing import Dict, Any, Optional, List
from models.problem_schema import Problem
from utils.database_manager import DatabaseManager
from . import ui_components
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from utils.task_id_utils import extract_task_id_and_form_id

logger = logging.getLogger(__name__)

class HTMLRenderer:
    """
    A class to render assignment data into an HTML string using Jinja2 templates.
    This class takes the dictionary of data produced by the scraper,
    prepares context data, and renders it using Jinja2 templates to generate
    complete HTML documents containing assignments, MathJax, and interactive forms.
    """
    def __init__(self, db_manager: DatabaseManager):
        self._css_clean_pattern = re.compile(r'[^\{\}]+\{\s*\}')
        self._answer_form_renderer = ui_components.AnswerFormRenderer()
        self._db_manager = db_manager
        logger.debug("HTMLRenderer initialized with DatabaseManager instance.")

        self._templates_dir = Path(__file__).parent.parent / "templates" / "ui_components"
        self._jinja_env = Environment(
            loader=FileSystemLoader(self._templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        logger.debug(f"Jinja2 Environment for HTMLRenderer initialized with template directory: {self._templates_dir}")

    def render_block_from_problem(self, problem: Problem, block_index: int) -> str:
        """
        Renders a single assignment block HTML string using the 'single_block_page.html.j2' template,
        based SOLELY on the structured Problem data (problem.text).
        offline_html is IGNORED and no longer used.
        """
        logger.info(f"Rendering HTML block from Problem.text for block_index: {block_index}, problem_id: {problem.problem_id}")
        try:
            task_id, form_id = extract_task_id_and_form_id(problem.problem_id)
            logger.debug(f"Extracted task_id: {task_id}, form_id: {form_id} from problem_id: {problem.problem_id}")

            # ВСЕГДА используем problem.text — offline_html больше не существует
            processed_block_html_content = problem.text

            rendered_html = self.render_block(
                block_html=processed_block_html_content,
                block_index=block_index,
                task_id=task_id,
                form_id=form_id,
                page_name=problem.problem_id
            )
            logger.info(f"Successfully rendered HTML block from Problem.text for block_index {block_index}")
            return rendered_html
        except Exception as e:
            logger.error(f"Error rendering HTML block from Problem.text for block_index {block_index} (problem_id {problem.problem_id}): {e}", exc_info=True)
            raise

    def render(self, data: Optional[Dict[str, Any]], page_name: str, problems: Optional[List[Problem]] = None) -> str:
        try:
            blocks_html = []
            task_metadata = []
            if problems is not None:
                logger.debug("Using provided List[Problem] for rendering initial state.")
                initial_state = {}
                for problem in problems:
                    task_id = problem.problem_id
                    user_answer, status = self._db_manager.get_answer_and_status(task_id=task_id)
                    if user_answer is not None or status != "not_checked":
                        initial_state[task_id] = {"answer": user_answer, "status": status}
                if data is not None:
                    blocks_html = data.get("blocks_html", [])
                    task_metadata = data.get("task_metadata", [])
                else:
                    logger.warning("data is None and problems do not contain HTML blocks. blocks_html will be empty.")
            else:
                logger.warning("List[Problem] not provided to render. Falling back to using 'data' dictionary.")
                if data is None:
                     raise ValueError("If 'problems' is None, 'data' must be provided.")
                blocks_html = data.get("blocks_html", [])
                task_metadata = data.get("task_metadata", [])
                task_ids = [metadata.get('task_id', '') for metadata in task_metadata if metadata.get('task_id')]
                logger.debug(f"Fetching initial state for {len(task_ids)} task IDs for page {page_name}. Task IDs: {task_ids[:5]}...")
                initial_state = self._get_filtered_initial_state_from_db(task_ids)
                logger.debug(f"Retrieved initial state for {len(initial_state)} tasks for page {page_name}.")

            page_data = {"page_name": page_name, "subject_name": "ЕГЭ"}
            initial_state_json = json.dumps(initial_state, ensure_ascii=False, indent=2)
            initial_state_js = f"<script>\nvar INITIAL_PAGE_STATE = {initial_state_json};\n</script>\n"

            task_blocks_data = []
            for idx, block_html in enumerate(blocks_html):
                metadata = task_metadata[idx] if idx < len(task_metadata) else {}
                task_id = metadata.get('task_id', '')
                form_id = metadata.get('form_id', '')
                form_html = self._answer_form_renderer.render(idx)
                block_wrapper_html = f"<div class='processed_qblock' id='processed_qblock_{idx}' data-task-id='{task_id}' data-form-id='{form_id}'>{block_html}\n{form_html}\n</div>\n<hr>\n"
                task_blocks_data.append({"index": idx, "html": block_wrapper_html})

            template_context = {
                "page_data": page_data,
                "task_blocks": task_blocks_data,
                "initial_state_js": initial_state_js,
                "common_css": ui_components.COMMON_CSS,
                "common_js_functions": ui_components.COMMON_JS_FUNCTIONS,
                "lang": "ru"
            }

            template = self._jinja_env.get_template("full_page.html.j2")
            result_html = template.render(template_context)
            logger.info(f"Successfully rendered HTML for page {page_name}, length: {len(result_html)} characters.")
            return result_html
        except Exception as e:
            logger.error(f"Error rendering HTML for page {page_name}: {e}", exc_info=True)
            raise

    def render_block(self, block_html: str, block_index: int, asset_path_prefix: Optional[str] = None, task_id: Optional[str] = "", form_id: Optional[str] = "", page_name: Optional[str] = None) -> str:
        try:
            logger.info(f"Rendering HTML block for block_index: {block_index}, task_id: {task_id}, page_name: {page_name}")

            initial_state = {}
            if task_id:
                logger.debug(f"Fetching initial state for block {block_index} using task_id: {task_id}")
                user_answer, status = self._db_manager.get_answer_and_status(task_id=task_id)
                if user_answer is not None or status != "not_checked":
                    initial_state = {task_id: {"answer": user_answer, "status": status}}
                    logger.debug(f"Retrieved initial state for block {block_index} (task_id {task_id}): {initial_state}")

            processed_block_html = block_html
            if asset_path_prefix:
                pattern = r'((src|href)\s*=\s*["\'])assets/([^"\']*)(["\'])'
                def replace_path(match):
                    prefix = asset_path_prefix
                    if not prefix.endswith('/'):
                        prefix += '/'
                    return f"{match.group(1)}{prefix}{match.group(3)}{match.group(4)}"
                processed_block_html = re.sub(pattern, replace_path, block_html)
            else:
                logger.debug("No asset_path_prefix provided for render_block. Paths to assets in block HTML will remain unchanged.")

            initial_state_json = json.dumps(initial_state, ensure_ascii=False, indent=2)
            initial_state_js = f"<script>\nvar INITIAL_PAGE_STATE = {initial_state_json};\n</script>\n"

            form_html = self._answer_form_renderer.render(block_index)
            wrapped_block_html = f"<div class='processed_qblock' id='processed_qblock_{block_index}' data-task-id='{task_id}' data-form-id='{form_id}'>{processed_block_html}\n{form_html}\n</div>"

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

            template = self._jinja_env.get_template("single_block_page.html.j2")
            result_html = template.render(template_context)
            logger.info(f"Successfully rendered HTML for block {block_index}, length: {len(result_html)} characters.")
            return result_html
        except Exception as e:
            logger.error(f"Error rendering HTML for block {block_index} (task_id {task_id}): {e}", exc_info=True)
            raise

    def save(self, html_string: str, path: str) -> None:
        try:
            logger.info(f"Saving HTML string to path: {path}, length: {len(html_string)} characters.")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html_string)
        except Exception as e:
            logger.error(f"Error saving HTML to path {path}: {e}", exc_info=True)
            raise

    def _clean_css(self, css_text: str) -> str:
        return self._css_clean_pattern.sub('', css_text)

    def _get_filtered_initial_state_from_db(self, task_ids: list[str]) -> dict:
        logger.debug(f"Fetching initial state from DB for {len(task_ids)} task IDs: {task_ids[:5]}...")
        initial_state = {}
        for task_id in task_ids:
            if task_id:
                logger.debug(f"Fetching state for individual task_id: {task_id}")
                user_answer, status = self._db_manager.get_answer_and_status(task_id=task_id)
                logger.debug(f"Fetched state for {task_id}: answer present = {user_answer is not None}, status = {status}")
                if user_answer is not None or status != "not_checked":
                    initial_state[task_id] = {"answer": user_answer, "status": status}
        logger.debug(f"Aggregated initial state for {len(initial_state)} tasks out of {len(task_ids)} requested.")
        return initial_state
