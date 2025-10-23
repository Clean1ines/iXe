# processors/ui_components.py
"""
Module for rendering reusable UI components for HTML pages.

This module provides classes and functions to generate common UI elements
like math symbol buttons, answer forms, and task info components.
"""

from typing import Optional
import html


class MathSymbolButtonsRenderer:
    """
    Renders HTML and JavaScript for a set of math symbol buttons.
    """

    @staticmethod
    def render(block_index: int, active: bool = False) -> str:
        """
        Generates the HTML for the math symbol buttons.

        Args:
            block_index (int): The index of the assignment block.
            active (bool): Whether the buttons div should be initially visible.

        Returns:
            str: The HTML string for the math buttons div.
        """
        active_class = " active" if active else ""
        # The onclick handlers call the global JS functions defined in HTMLRenderer
        return f'''<div class="math-buttons{active_class}">
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
    <button type="button" onclick="insertSymbol({block_index}, '\\\\sqrt{{}}')">√( )</button>
    <button type="button" onclick="insertSymbol({block_index}, '{{{{}}}}^{{{{}}}}')">^( , )</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\frac{{{{}}}}{{{{}}}}')">frac</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\log_{{{{}}}}{{{{}}}}')">log_b( )</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\lim_{{x \\\\to }}')">lim</button>
    <button type="button" onclick="insertSymbol({block_index}, \"f'(x)\")">f'(x)</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\int {{{{}}}} dx')">∫ dx</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\sum')">∑</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\in')">∈</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\cup')">∪</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\cap')">∩</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\emptyset')">∅</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\to')">→</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\Rightarrow')">⇒</button>
    <button type="button" onclick="insertSymbol({block_index}, '\\\\Leftrightarrow')">⇔</button>
  </div>'''

class AnswerFormRenderer:
    """
    Renders the HTML for the interactive answer form for a specific block.
    """

    def __init__(self):
        """
        Initializes the AnswerFormRenderer.
        """
        self.math_buttons_renderer = MathSymbolButtonsRenderer()

    def render(self, block_index: int) -> str:
        """
        Generates the HTML for the interactive answer form for a specific block.

        Args:
            block_index (int): The index of the assignment block.

        Returns:
            str: The HTML string for the form.
        """
        # Use the MathSymbolButtonsRenderer to get the button HTML
        math_buttons_html = self.math_buttons_renderer.render(block_index, active=False)

        return f'''<form class="answer-form" onsubmit="submitAnswer(event, {block_index})">
  <label for="answer_{block_index}">Ваш ответ:</label>
  <input type="text" id="answer_{block_index}" name="answer" maxlength="250" size="40" placeholder="Введите/соберите ответ">
  <button type="button" class="toggle-math-btn" onclick="toggleMathButtons(this)">Показать/скрыть математические символы</button>
  {math_buttons_html}
  <button type="submit">Отправить ответ</button>
</form>'''

# Optional: Define common CSS here if not using an external file
COMMON_CSS = """
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

# Optional: Define common JS functions here if not using an external file
COMMON_JS_FUNCTIONS = """
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