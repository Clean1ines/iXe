# processors/ui_components.py
"""
Module for rendering reusable UI components for HTML pages.

This module provides classes and functions to generate common UI elements
like math symbol buttons, answer forms, and task info components.
"""

import logging
from typing import Optional
import html


logger = logging.getLogger(__name__)


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
        logger.debug(f"Rendering MathSymbolButtons for block_index: {block_index}, active: {active}")
        active_class = " active" if active else ""
        # The onclick handlers call the global JS functions defined in HTMLRenderer
        html_content = f'''<div class="math-buttons{active_class}">
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
        Generates the HTML for the interactive answer form for a specific block.

        Args:
            block_index (int): The index of the assignment block.

        Returns:
            str: The HTML string for the form.
        """
        logger.debug(f"Rendering AnswerForm for block_index: {block_index}")
        # Use the MathSymbolButtonsRenderer to get the button HTML
        logger.debug(f"Generating MathSymbolButtons HTML for AnswerForm block_index: {block_index}")
        math_buttons_html = self.math_buttons_renderer.render(block_index, active=False)
        logger.debug(f"Generated MathSymbolButtons HTML for AnswerForm block_index: {block_index}, length: {len(math_buttons_html)} characters")

        # Используем block_index как placeholder для task_id и form_id.
        # Эти значения будут заменены в html_renderer при генерации итогового HTML.
        # Также добавляем div для отображения статуса проверки.
        html_content = f'''<form class="answer-form" onsubmit="submitAnswerAndCheck(event, {block_index})">
  <label for="answer_{block_index}">Ваш ответ:</label>
  <input type="text" id="answer_{block_index}" name="answer" maxlength="250" size="40" placeholder="Введите/соберите ответ">
  <button type="button" class="toggle-math-btn" onclick="toggleMathButtons(this)">Показать/скрыть математические символы</button>
  {math_buttons_html}
  <button type="submit">Отправить ответ</button>
</form>
<div class="task-status" id="task-status-{block_index}"></div>'''
        logger.debug(f"Generated HTML for AnswerForm block_index: {block_index}, length: {len(html_content)} characters")
        return html_content

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
/* Стили для статуса задания */
.task-status {
    margin-top: 5px;
    padding: 5px;
    font-weight: bold;
}
.task-status-2 { /* Incorrect */
    background-color: #ffe6e6;
    color: #d00;
    border: 1px solid #ffcccc;
}
.task-status-3 { /* Correct */
    background-color: #e6ffe6;
    color: #080;
    border: 1px solid #ccffcc;
}
.task-status-error { /* Error */
    background-color: #fff0e6;
    color: #ff6600;
    border: 1px solid #ffccaa;
}
"""

# Optional: Define common JS functions here if not using an external file
COMMON_JS_FUNCTIONS = """function insertSymbol(blockIndex, symbol) {
  const input = document.querySelector(`#answer_` + blockIndex);
  const start = input.selectionStart;
  const end = input.selectionEnd;
  const val = input.value;
  input.value = val.substring(0, start) + symbol + val.substring(end);
  input.selectionStart = input.selectionEnd = start + symbol.length;
  input.focus();
}


// ИСПРАВЛЕНО: Новая асинхронная функция для отправки и проверки ответа через backend
async function submitAnswerAndCheck(event, blockIndex) {
  event.preventDefault(); // Предотвращаем стандартную отправку формы

  // Находим элемент блока и извлекаем data-атрибуты
  const blockElement = document.querySelector(`#processed_qblock_` + blockIndex);
  const taskId = blockElement.getAttribute('data-task-id');
  const formId = blockElement.getAttribute('data-form-id');
  const input = document.querySelector(`#answer_` + blockIndex);
  const userAnswer = input.value.trim();

  if (!userAnswer) {
    alert("Пожалуйста, введите ответ.");
    return;
  }

  if (!taskId || !formId) {
    alert("Ошибка: Не найдены идентификаторы задания или формы.");
    console.error("Missing taskId or formId for block index:", blockIndex);
    return;
  }

  // Показываем статус "проверка"
  const statusDiv = document.querySelector(`#task-status-` + blockIndex);
  statusDiv.textContent = "Проверка...";
  statusDiv.className = "task-status"; // Сбрасываем классы статуса

  try {
    // Отправляем запрос на ваш backend endpoint
    // ЗАМЕНИТЕ 'http://localhost:8000' на реальный URL вашего API
    const response = await fetch('http://localhost:8000/submit_answer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_id: taskId,
        answer: userAnswer,
        form_id: formId,
      }),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: \${response.status}`);
    }

    const data = await response.json();

    // Обновляем статус в зависимости от ответа от backend
    if (data.status === 'correct') {
      statusDiv.textContent = data.message || "ВЕРНО";
      statusDiv.classList.add('task-status-3'); // Класс для "correct"
    } else if (data.status === 'incorrect') {
      statusDiv.textContent = data.message || "НЕВЕРНО";
      statusDiv.classList.add('task-status-2'); // Класс для "incorrect"
    } else {
      statusDiv.textContent = "Неизвестный статус от сервера.";
      statusDiv.classList.add('task-status-error'); // Можно добавить стиль для ошибки
    }
  } catch (error) {
    console.error("Ошибка при проверке ответа:", error);
    statusDiv.textContent = "Ошибка сети или сервера при проверке.";
    statusDiv.classList.add('task-status-error');
  }
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

    // Загрузка начального состояния из глобальной переменной INITIAL_PAGE_STATE
    // Эта переменная должна быть вставлена в HTML при генерации
    if (typeof INITIAL_PAGE_STATE === 'object' && INITIAL_PAGE_STATE !== null) {
        loadInitialStateFromObject(INITIAL_PAGE_STATE);
    } else {
        console.warn("INITIAL_PAGE_STATE не определена. Состояние не будет загружено из локального хранилища при загрузке.");
    }
});

// Новая функция для загрузки начального состояния из переданного объекта
function loadInitialStateFromObject(state) {
    // Перебираем все блоки заданий на странице
    document.querySelectorAll('.processed_qblock').forEach(block => {
        const taskId = block.getAttribute('data-task-id');
        if (taskId && state[taskId]) {
            const storedData = state[taskId];
            const blockIndex = parseInt(block.id.replace('processed_qblock_', ''));
            const input = document.querySelector(`#answer_\${blockIndex}`);
            const statusDiv = document.querySelector(`#task-status-\${blockIndex}`);

            // Устанавливаем сохранённый ответ в поле ввода
            if (input && storedData.answer) {
                input.value = storedData.answer;
            }

            // Устанавливаем сохранённый статус
            if (statusDiv) {
                statusDiv.textContent = storedData.status === 'correct' ? "Сохранено: ВЕРНО" :
                                       storedData.status === 'incorrect' ? "Сохранено: НЕВЕРНО" :
                                       storedData.status === 'not_checked' ? "Сохранено: Не проверено" : "Сохранено: " + storedData.status;
                // Убираем предыдущие классы статуса
                statusDiv.classList.remove('task-status-2', 'task-status-3', 'task-status-error');
                // Добавляем соответствующий класс
                if (storedData.status === 'correct') {
                    statusDiv.classList.add('task-status-3');
                } else if (storedData.status === 'incorrect') {
                    statusDiv.classList.add('task-status-2');
                } else {
                    // Для 'not_checked' или других статусов можно добавить общий класс или оставить без специфического
                    // statusDiv.classList.add('task-status-not-checked'); // Если такой стиль добавлен
                }
            }
        }
    });
}
"""

