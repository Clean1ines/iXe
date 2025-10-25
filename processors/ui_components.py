# processors/ui_components.py
"""
Module for rendering reusable UI components for HTML pages.

This module provides classes and functions to generate common UI elements
like math symbol buttons, answer forms, and task info components.
"""

import logging
from typing import Optional
import html
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path


logger = logging.getLogger(__name__)

# --- Jinja2 Setup ---
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "ui_components"
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)
logger.debug(f"Jinja2 Environment initialized with template directory: {TEMPLATES_DIR}")
# --------------------

# Load CSS and JS from templates
common_css_template = jinja_env.get_template("common_styles.css")
COMMON_CSS = common_css_template.render()
common_js_template = jinja_env.get_template("common_scripts.js")
COMMON_JS_FUNCTIONS = common_js_template.render()
logger.debug("Loaded COMMON_CSS and COMMON_JS_FUNCTIONS from templates.")

class MathSymbolButtonsRenderer:
    """
    Renders HTML and JavaScript for a set of math symbol buttons.
    """

    @staticmethod
    def render(block_index: int, active: bool = False) -> str:
        """
        Generates the HTML for the math symbol buttons using a Jinja2 template.

        Args:
            block_index (int): The index of the assignment block.
            active (bool): Whether the buttons div should be initially visible.

        Returns:
            str: The HTML string for the math buttons div.
        """
        logger.debug(f"Rendering MathSymbolButtons for block_index: {block_index}, active: {active}")
        template = jinja_env.get_template("math_symbol_buttons.html.j2")
        html_content = template.render(block_index=block_index, active=active)
        logger.debug(f"Generated HTML for MathSymbolButtons, length: {len(html_content)} characters")
        return html_content

class AnswerFormRenderer:
    """
    Renders the HTML for the interactive answer form for a specific block.
    """

    def __init__(self):
        """
        Initializes the AnswerFormRenderer.
        """
        self.math_buttons_renderer = MathSymbolButtonsRenderer()
        logger.debug("AnswerFormRenderer initialized with MathSymbolButtonsRenderer instance")

    def render(self, block_index: int) -> str:
        """
        Generates the HTML for the interactive answer form for a specific block using a Jinja2 template.

        Args:
            block_index (int): The index of the assignment block.

        Returns:
            str: The HTML string for the form.
        """
        logger.debug(f"Rendering AnswerForm for block_index: {block_index}")
        # Pass the MathSymbolButtonsRenderer instance to the template context
        template = jinja_env.get_template("answer_form.html.j2")
        html_content = template.render(
            block_index=block_index,
            math_buttons_renderer=self.math_buttons_renderer
        )
        logger.debug(f"Generated HTML for AnswerForm block_index: {block_index}, length: {len(html_content)} characters")
        return html_content

