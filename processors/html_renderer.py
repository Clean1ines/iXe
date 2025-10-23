# processors/html_renderer.py
"""
Module for rendering scraped data into HTML format.

This module provides the `HTMLRenderer` class which takes processed data
from the scraper and generates a complete HTML document.
"""

import re
from typing import Dict, Any


class HTMLRenderer:
    """
    A class to render assignment data into an HTML string.

    This class takes the dictionary of data produced by the scraper and
    generates a single HTML file containing the assignments, MathJax for
    rendering formulas, and interactive answer forms.
    """

    def __init__(self):
        """
        Initializes the HTMLRenderer.
        """
        # Pre-compile the CSS cleaning regex for efficiency if used multiple times
        self._css_clean_pattern = re.compile(r'[^\{\}]+\{\s*\}')

    # ИСПРАВЛЕНО: Добавлено имя аргумента 'data'
    def render(self, data: Dict[str, Any]) -> str:
        """
        Renders the provided data dictionary into an HTML string for the entire page.

        Args:
            data (Dict[str, Any]): The data dictionary from the scraper.
                                   Expected keys: 'page_name', 'blocks_html', 'assignments', 'images', 'files'.

        Returns:
            str: The complete HTML string for the page.
        """
        page_name = data.get("page_name", "unknown")
        blocks_html = data.get("blocks_html", [])

        # Clean CSS (example logic, can be expanded)
        raw_css = """
.processed_qblock {margin:20px;padding:10px;border:1px solid #ccc;}
img{max-width:100%;height:auto;}
.answer-form { margin-top: 10px; padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd; }
.math-buttons { margin-top: 5px; display: none; } /* Скрыто по умолчанию */
.math-buttons.active { display: block; } /* Показывается при добавлении класса 'active' */
.math-buttons button { margin: 2px; padding: 3px 6px; font-size: 12px; }
/* Добавим стили для информационного блока */
.task-info-content { margin-top: 10px; padding: 10px; background-color: #eef; border: 1px solid #ccc; display: none; } /* Скрыт по умолчанию */
.show-info .task-info-content { display: block; } /* Показывается при добавлении класса show-info */
.info-button { display: inline-block; width: 20px; height: 20px; line-height: 20px; text-align: center; background-color: #ccc; color: white; border-radius: 50%; cursor: pointer; margin-left: 10px; }
/* Стили для таблицы информации */
.task-info-content table { width: 100%; border-collapse: collapse; }
.task-info-content td { border: 1px solid #ccc; padding: 5px; vertical-align: top; }
.task-info-content .param-name { font-weight: bold; width: 150px; background-color: #eee; }
.toggle-math-btn { margin-bottom: 5px; }
        """
        cleaned_css = self._clean_css(raw_css)

        # Start building the HTML string
        html_parts = [
            "<!DOCTYPE html>\n<html lang='ru'>\n<head>\n<meta charset='utf-8'>\n",
            f"<title>FIPI Page {page_name}</title>\n",
            f"<style>{cleaned_css}</style>\n",
            "<script src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML'></script>\n",
            "<script>\n",
            self._get_js_functions(), # Get the required JS functions as a string
            "</script>\n",
            "</head>\n<body>\n"
        ]

        for idx, block_html in enumerate(blocks_html):
            # Wrap each block in a div and add the interactive form
            # Note: The info-button and task-info-content should already be part of block_html from scraper
            # The form now includes a toggle button for math buttons and the math buttons div itself
            form_html = self._get_answer_form_html(idx)
            # The scraper should have already included the info content and button in block_html
            # We just add the form after the block content
            full_block_html = f"<div class='processed_qblock' id='processed_qblock_{idx}'>\n{block_html}\n{form_html}\n</div>\n<hr>\n"
            html_parts.append(full_block_html)

        html_parts.append("</body>\n</html>")
        return "".join(html_parts)

    # ИСПРАВЛЕНО: Новый метод render_block
    def render_block(self, block_html: str, block_index: int) -> str:
        """
        Renders a single assignment block HTML string.

        Args:
            block_html (str): The raw HTML content of the assignment block.
            block_index (int): The index of the block for form/ID generation.

        Returns:
            str: The complete HTML string for the single block, including MathJax and form.
        """
        # Use the same CSS and JS as the page-level render, but only wrap the single block
        raw_css = """
.processed_qblock {margin:20px;padding:10px;border:1px solid #ccc;}
img{max-width:100%;height:auto;}
.answer-form { margin-top: 10px; padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd; }
.math-buttons { margin-top: 5px; display: none; } /* Скрыто по умолчанию */
.math-buttons.active { display: block; } /* Показывается при добавлении класса 'active' */
.math-buttons button { margin: 2px; padding: 3px 6px; font-size: 12px; }
/* Добавим стили для информационного блока */
.task-info-content { margin-top: 10px; padding: 10px; background-color: #eef; border: 1px solid #ccc; display: none; } /* Скрыт по умолчанию */
.show-info .task-info-content { display: block; } /* Показывается при добавлении класса show-info */
.info-button { display: inline-block; width: 20px; height: 20px; line-height: 20px; text-align: center; background-color: #ccc; color: white; border-radius: 50%; cursor: pointer; margin-left: 10px; }
/* Стили для таблицы информации */
.task-info-content table { width: 100%; border-collapse: collapse; }
.task-info-content td { border: 1px solid #ccc; padding: 5px; vertical-align: top; }
.task-info-content .param-name { font-weight: bold; width: 150px; background-color: #eee; }
.toggle-math-btn { margin-bottom: 5px; }
        """
        # No need to clean CSS for single block if it's static, but we can reuse the logic
        cleaned_css = self._clean_css(raw_css)

        html_parts = [
            "<!DOCTYPE html>\n<html lang='ru'>\n<head>\n<meta charset='utf-8'>\n",
            f"<title>FIPI Block {block_index}</title>\n", # Different title
            f"<style>{cleaned_css}</style>\n",
            "<script src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML'></script>\n",
            "<script>\n",
            self._get_js_functions(),
            "</script>\n",
            "</head>\n<body>\n",
            # Wrap the single block
            f"<div class='processed_qblock' id='processed_qblock_{block_index}'>\n{block_html}\n",
            # Add the form for this specific block
            self._get_answer_form_html(block_index),
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

    def _get_js_functions(self) -> str:
        """
        Returns the required JavaScript functions as a string.

        These functions handle inserting math symbols, submitting answers,
        toggling the visibility of math buttons, and the task info block.

        Returns:
            str: The JavaScript code as a string.
        """
        # ИСПРАВЛЕНО: Добавлены функции toggleMathButtons, toggleInfo
        return """
function insertSymbol(blockIndex, symbol) {
  const input = document.querySelector(`#answer_` + blockIndex);
  const start = input.selectionStart;
  const end = input.selectionEnd;
  const val = input.value;
  input.value = val.substring(0, start) + symbol + val.substring(end);
  input.selectionStart = input.selectionEnd = start + symbol.length;
  input.focus();
}

function submitAnswer(event, blockIndex) {
  event.preventDefault();
  const input = document.querySelector(`#answer_` + blockIndex);
  const answer = input.value;
  alert("Ответ для задания " + blockIndex + " сохранен локально: " + answer);
  // Here you could add logic to save the answer to JSON or another storage
}

// ИСПРАВЛЕНО: Добавлена функция toggleMathButtons
function toggleMathButtons(button) {
    const block = button.closest('.processed_qblock');
    const mathButtonsDiv = block.querySelector('.math-buttons');
    mathButtonsDiv.classList.toggle('active');
}

// ИСПРАВЛЕНО: Добавлена функция toggleInfo
function toggleInfo(button) {
    const block = button.closest('.processed_qblock');
    block.classList.toggle('show-info');
}

// ИСПРАВЛЕНО: Инициализация кнопок info при загрузке
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.info-button').forEach(button => {
        button.onclick = function() { toggleInfo(this); };
    });
});

"""

    def _get_answer_form_html(self, block_index: int) -> str:
        """
        Generates the HTML for the interactive answer form for a specific block.

        Args:
            block_index (int): The index of the assignment block.

        Returns:
            str: The HTML string for the form.
        """
        # This is the large form HTML string from the original code
        # ЗАКРЫВАЕМ f-string правильно
        # ИСПРАВЛЕНО: Добавлена кнопка для переключения видимости math-buttons и div для math-buttons с классом 'math-buttons'
        return f'''<form class="answer-form" onsubmit="submitAnswer(event, {block_index})">
  <label for="answer_{block_index}">Ваш ответ:</label>
  <input type="text" id="answer_{block_index}" name="answer" maxlength="250" size="40" placeholder="Введите/соберите ответ">
  <button type="button" class="toggle-math-btn" onclick="toggleMathButtons(this)">Показать/скрыть математические символы</button>
  <div class="math-buttons">
    <!-- Основные символы -->
    <button type="button" onclick="insertSymbol({block_index}, '+')">+</button>
    <button type="button" onclick="insertSymbol({block_index}, '−')">−</button>
    <button type="button" onclick="insertSymbol({block_index}, '×')">×</button>
    <button type="button" onclick="insertSymbol({block_index}, '÷')">÷</button>
    <button type="button" onclick="insertSymbol({block_index}, '=')">=</button>
    <button type="button" onclick="insertSymbol({block_index}, '<')"><</button>
    <button type="button" onclick="insertSymbol({block_index}, '>')">></button>
    <button type="button" onclick="insertSymbol({block_index}, '≠')">≠</button>
    <button type="button" onclick="insertSymbol({block_index}, '≤')">≤</button>
    <button type="button" onclick="insertSymbol({block_index}, '≥')">≥</button>
    <button type="button" onclick="insertSymbol({block_index}, '%')">%</button>
    <br>
    <!-- Степень и корень -->
    <button type="button" onclick="insertSymbol({block_index}, '^')">x^y</button>
    <button type="button" onclick="insertSymbol({block_index}, '√')">√x</button>
    <button type="button" onclick="insertSymbol({block_index}, '∛')">∛x</button>
    <button type="button" onclick="insertSymbol({block_index}, '∜')">∜x</button>
    <br>
    <!-- Греческие буквы -->
    <button type="button" onclick="insertSymbol({block_index}, 'α')">α</button>
    <button type="button" onclick="insertSymbol({block_index}, 'β')">β</button>
    <button type="button" onclick="insertSymbol({block_index}, 'γ')">γ</button>
    <button type="button" onclick="insertSymbol({block_index}, 'π')">π</button>
    <button type="button" onclick="insertSymbol({block_index}, 'θ')">θ</button>
    <button type="button" onclick="insertSymbol({block_index}, 'φ')">φ</button>
    <button type="button" onclick="insertSymbol({block_index}, '∞')">∞</button>
    <br>
    <!-- Функции -->
    <button type="button" onclick="insertSymbol({block_index}, 'sin')">sin</button>
    <button type="button" onclick="insertSymbol({block_index}, 'cos')">cos</button>
    <button type="button" onclick="insertSymbol({block_index}, 'tan')">tan</button>
    <button type="button" onclick="insertSymbol({block_index}, 'log')">log</button>
    <button type="button" onclick="insertSymbol({block_index}, 'ln')">ln</button>
    <button type="button" onclick="insertSymbol({block_index}, 'lg')">lg</button>
    <br>
    <!-- Конструкции (LaTeX-подобные, понятные MathJax) -->
    <button type="button" onclick="insertSymbol({block_index}, '\\sqrt{{}}')">√( )</button>
    <button type="button" onclick="insertSymbol({block_index}, '{{}}^{{}}')">^( , )</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\frac{{}} {{}}')">frac</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\log_{{}} {{}}')">log_b( )</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\lim_{{x \\to }}')">lim</button>
    <button type="button" onclick="insertSymbol({block_index}, 'f\'(x)')">f'(x)</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\int {{}} dx')">∫ dx</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\sum')">∑</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\in')">∈</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\cup')">∪</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\cap')">∩</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\emptyset')">∅</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\to')">→</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\Rightarrow')">⇒</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\Leftrightarrow')">⇔</button>
  </div>
  <button type="submit">Отправить ответ</button>
</form>'''
        # f-string теперь корректно закрыт тремя кавычками '''

