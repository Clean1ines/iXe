function insertSymbol(blockIndex, symbol) {
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
        throw new Error(`HTTP error! status: ${response.status}`);
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
            const input = document.querySelector(`#answer_${blockIndex}`);
            const statusDiv = document.querySelector(`#task-status-${blockIndex}`);

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
