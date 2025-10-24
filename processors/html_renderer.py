# processors/html_renderer.py
"""
Module for rendering scraped data into HTML format.

This module provides the `HTMLRenderer` class which takes processed data
from the scraper and generates a complete HTML document.
It now delegates UI component rendering to `ui_components.py`.
"""

import re
from typing import Dict, Any, Optional
from . import ui_components # Импортируем модуль с компонентами
from utils.local_storage import LocalStorage


class HTMLRenderer:
    """
    A class to render assignment data into an HTML string.

    This class takes the dictionary of data produced by the scraper and
    generates a single HTML file containing the assignments, MathJax for
    rendering formulas, and interactive answer forms.
    """

    def __init__(self, storage: LocalStorage): # NEW: Принимаем storage
        """
        Initializes the HTMLRenderer.
        """
        # Pre-compile the CSS cleaning regex for efficiency if used multiple times
        self._css_clean_pattern = re.compile(r'[^\{\}]+\{\s*\}')
        self._answer_form_renderer = ui_components.AnswerFormRenderer()
        self._storage = storage # NEW: Сохраняем storage

    def render(self, data: Dict[str, Any], page_name: str) -> str: # NEW: Принимаем page_name
        """
        Renders the provided data dictionary into an HTML string for the entire page.

        Args:
            data (Dict[str, Any]): The data dictionary from the scraper.
                                   Expected keys: 'page_name', 'blocks_html', 'task_metadata'.
            page_name (str): The name of the current page, used for initial state loading.

        Returns:
            str: The complete HTML string for the page.
        """
        # NEW: Загружаем начальное состояние для этой страницы
        initial_state = self._storage._load_data() # Получаем все данные
        # Фильтруем по префиксу page_name (или используем всю информацию, если page_name не используется как префикс)
        # Для простоты, передаем всё состояние, но JS будет использовать только нужные ему task_id
        page_initial_state = {k: v for k, v in initial_state.items() if k.startswith(page_name)}

        blocks_html = data.get("blocks_html", [])
        task_metadata = data.get("task_metadata", []) # Получаем метаданные

        # Use the common CSS and JS from ui_components
        cleaned_css = self._clean_css(ui_components.COMMON_CSS)

        # NEW: Генерируем JS для вставки глобальной переменной INITIAL_PAGE_STATE
        import json
        initial_state_json = json.dumps(page_initial_state, ensure_ascii=False, indent=2)
        initial_state_js = f"<script>\nvar INITIAL_PAGE_STATE = {initial_state_json};\n</script>\n"

        # Start building the HTML string
        html_parts = [
            "<!DOCTYPE html>\n<html lang='ru'>\n<head>\n<meta charset='utf-8'>\n",
            f"<title>FIPI Page {page_name}</title>\n",
            f"<style>{cleaned_css}</style>\n",
            "<script src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML'></script>\n",
            # NEW: Вставляем переменную INITIAL_PAGE_STATE перед COMMON_JS_FUNCTIONS
            initial_state_js,
            "<script>\n",
            ui_components.COMMON_JS_FUNCTIONS, # Use the common JS functions
            "</script>\n",
            "</head>\n<body>\n"
        ]

        for idx, block_html in enumerate(blocks_html):
            # Получаем метаданные для текущего блока
            metadata = task_metadata[idx] if idx < len(task_metadata) else {}
            task_id = metadata.get('task_id', '')
            form_id = metadata.get('form_id', '')

            # Встраиваем task_id и form_id как data-атрибуты в div.processed_qblock
            # Также используем атрибут id для идентификации блока
            block_wrapper_start = f"<div class='processed_qblock' id='processed_qblock_{idx}' data-task-id='{task_id}' data-form-id='{form_id}'>\n"

            # Render the answer form for this block
            form_html = self._answer_form_renderer.render(idx)
            # Wrap each block in a div and add the interactive form
            # The scraper should have already included the info content and button in block_html
            # We just add the form after the block content
            full_block_html = f"{block_wrapper_start}{block_html}\n{form_html}\n</div>\n<hr>\n"
            html_parts.append(full_block_html)

        html_parts.append("</body>\n</html>")
        return "".join(html_parts)

    def render_block(self, block_html: str, block_index: int, asset_path_prefix: Optional[str] = None, task_id: Optional[str] = "", form_id: Optional[str] = "", page_name: Optional[str] = None) -> str: # NEW: Принимаем page_name
        """
        Renders a single assignment block HTML string.

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
        # NEW: Загружаем начальное состояние для этой страницы (если page_name предоставлена)
        initial_state = {}
        if page_name:
            all_data = self._storage._load_data()
            initial_state = {k: v for k, v in all_data.items() if k.startswith(page_name)}

        # Use the common CSS and JS from ui_components
        cleaned_css = self._clean_css(ui_components.COMMON_CSS)

        # Adjust asset paths in block_html if prefix is provided
        processed_block_html = block_html
        if asset_path_prefix:
            # Example regex for <img src="..."> and <a href="...">
            # This is a basic example, might need refinement for other tags/attributes
            import re
            # ИСПРАВЛЕНО: Регулярное выражение теперь аккуратно захватывает только атрибут src или href
            # Ищем src="assets/..." или href="assets/..." (или с одинарными кавычками)
            # (\1) - захватывает src=" или href=" или src=' или href='
            # assets/ - искомый префикс
            # (\2) - захватывает оставшуюся часть пути
            # (\3) - захватывает закрывающую кавычку
            pattern = r'((src|href)\s*=\s*["\'])assets/([^"\']*)(["\'])'
            
            def replace_path(match):
                prefix = asset_path_prefix
                if not prefix.endswith('/'):
                    prefix += '/'
                # match.group(1) = "src=" или "href=" (с кавычкой)
                # match.group(3) = оставшаяся часть пути
                # match.group(4) = закрывающая кавычка
                return f"{match.group(1)}{prefix}{match.group(3)}{match.group(4)}"
            
            processed_block_html = re.sub(pattern, replace_path, block_html)

        # NEW: Генерируем JS для вставки глобальной переменной INITIAL_PAGE_STATE
        import json
        initial_state_json = json.dumps(initial_state, ensure_ascii=False, indent=2)
        initial_state_js = f"<script>\nvar INITIAL_PAGE_STATE = {initial_state_json};\n</script>\n"

        html_parts = [
            "<!DOCTYPE html>\n<html lang='ru'>\n<head>\n<meta charset='utf-8'>\n",
            f"<title>FIPI Block {block_index}</title>\n", # Different title
            f"<style>{cleaned_css}</style>\n",
            "<script src='    https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML'></script>\n",
            # NEW: Вставляем переменную INITIAL_PAGE_STATE перед COMMON_JS_FUNCTIONS
            initial_state_js,
            "<script>\n",
            ui_components.COMMON_JS_FUNCTIONS,
            "</script>\n",
            "</head>\n<body>\n",
            # Wrap the single block (with potentially adjusted paths)
            # Встраиваем task_id и form_id как data-атрибуты в div.processed_qblock
            f"<div class='processed_qblock' id='processed_qblock_{block_index}' data-task-id='{task_id}' data-form-id='{form_id}'>\n{processed_block_html}\n",
            # Add the form for this specific block
            self._answer_form_renderer.render(block_index),
            "\n</div>\n</body>\n</html>"
        ]
        return "".join(html_parts)


    def save(self, html_string: str, path: str) -> None:
        """
        Saves the provided HTML string to a file.

        Args:
            html_string (str): The HTML content to save.
            path (str): The file path where the HTML should be saved.
        """
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_string)

    def _clean_css(self, css_text: str) -> str:
        """
        Removes empty CSS rules from the provided CSS text.

        Args:
            css_text (str): The raw CSS string.

        Returns:
            str: The cleaned CSS string with empty rules removed.
        """
        return self._css_clean_pattern.sub('', css_text)

    # _get_js_functions and _get_answer_form_html are removed as their logic is now in ui_components
