import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Глобальные типы для MathJax и insertSymbol
declare global {
  interface Window {
    MathJax?: {
      Hub: {
        Queue: (args: any[]) => void;
      };
    };
    insertSymbol?: (blockIndex: number, symbol: string) => void;
  }
}

interface TaskBlock {
  html: string;
  taskId: string;
  formId: string;
  blockIndex: string;
}

const CalibrationPage: React.FC = () => {
  const [blocks, setBlocks] = useState<TaskBlock[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    console.log('[CalibrationPage] Запуск useEffect загрузки блоков');
    const loadRandomBlocks = async () => {
      try {
        console.log('[CalibrationPage] Начинаем загрузку случайных блоков');
        const totalCount = 978;
        const allIds = Array.from({ length: totalCount }, (_, i) => i);
        const shuffled = allIds.sort(() => 0.5 - Math.random());
        const selectedIds = shuffled.slice(0, 10);
        console.log('[CalibrationPage] Выбранные ID:', selectedIds);
        const loadedBlocks: TaskBlock[] = [];

        for (const id of selectedIds) {
          console.log(`[CalibrationPage] Загрузка блока ${id}`);
          // Проверяем сначала _init.html, затем обычный .html
          let res;
          let finalId = id.toString();
          let fetchUrl = `/blocks/math/block_${id}_init.html`;
          try {
            res = await fetch(fetchUrl);
            if (!res.ok) {
              console.log(`[CalibrationPage] _init файл не найден для ${id}, пробуем основной`);
              fetchUrl = `/blocks/math/block_${id}.html`;
              res = await fetch(fetchUrl);
              if (!res.ok) {
                console.log(`[CalibrationPage] Основной файл также не найден для ${id}, пропускаем`);
                continue;
              }
              finalId = id.toString();
            } else {
              finalId = `${id}_init`;
            }
          } catch (fetchErr) {
            console.error(`[CalibrationPage] Ошибка fetch для ${id}:`, fetchErr);
            // Пробуем основной файл
            fetchUrl = `/blocks/math/block_${id}.html`;
            res = await fetch(fetchUrl);
            if (!res.ok) {
              console.log(`[CalibrationPage] Основной файл также не найден для ${id}, пропускаем`);
              continue;
            }
            finalId = id.toString();
          }

          console.log(`[CalibrationPage] Успешно загружен ${fetchUrl} для ID ${id}`);
          const html = await res.text();
          console.log(`[CalibrationPage] HTML содержимое для ID ${id} (первые 200 символов):`, html.substring(0, 200) + '...');

          const tempDiv = document.createElement('div');
          tempDiv.innerHTML = html;

          const qblock = tempDiv.querySelector('.processed_qblock');
          console.log(`[CalibrationPage] Найден processed_qblock для ID ${id}:`, qblock !== null);

          if (qblock) { // Проверяем, что qblock найден
            const taskId = qblock.getAttribute('data-task-id') || 'unknown';
            const formId = qblock.getAttribute('data-form-id') || '';
            const blockIndex = qblock.id?.replace('processed_qblock_', '') || finalId;

            console.log(`[CalibrationPage] taskId: ${taskId}, formId: ${formId}, blockIndex: ${blockIndex}`);
            loadedBlocks.push({ html, taskId, formId, blockIndex });
          } else {
            console.warn(`[CalibrationPage] processed_qblock не найден в HTML для ID ${id}`);
          }
        }
        console.log('[CalibrationPage] Загруженные блоки:', loadedBlocks);
        setBlocks(loadedBlocks);
      } catch (err) {
        console.error('[CalibrationPage] Критическая ошибка загрузки блоков:', err);
      } finally {
        setLoading(false);
        console.log('[CalibrationPage] Загрузка завершена, состояние loading изменено на false');
      }
    };

    loadRandomBlocks();
  }, []);

  const handleSubmit = async (
    e: React.FormEvent,
    taskId: string,
    formId: string,
    blockIndex: string
  ) => {
    console.log('[CalibrationPage] handleSubmit вызван для блока', blockIndex);
    e.preventDefault();
    const input = document.querySelector<HTMLInputElement>(`#answer_${blockIndex}`);
    console.log('[CalibrationPage] Найден input для блока', blockIndex, ':', input !== null);
    const userAnswer = input?.value.trim();
    if (!userAnswer) {
      alert('Введите ответ');
      return;
    }

    const statusEl = document.querySelector<HTMLDivElement>(`#task-status-${blockIndex}`);
    if (statusEl) {
      statusEl.textContent = 'Проверка...';
      statusEl.className = 'task-status';
    }

    try {
      const res = await fetch('https://ixe-core.onrender.com/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_id: taskId, user_answer: userAnswer, form_id: formId }),
      });
      const data = await res.json();
      console.log('[CalibrationPage] Ответ от сервера для', blockIndex, ':', data);
      if (statusEl) {
        if (data.verdict === 'correct') {
          statusEl.textContent = 'ВЕРНО';
          statusEl.className = 'task-status task-status-3';
        } else if (data.verdict === 'incorrect') {
          statusEl.textContent = 'НЕВЕРНО';
          statusEl.className = 'task-status task-status-2';
        } else {
          statusEl.textContent = 'Ошибка';
          statusEl.className = 'task-status task-status-error';
        }
      }
    } catch (err) {
      console.error('[CalibrationPage] Ошибка при отправке ответа для', blockIndex, ':', err);
      if (statusEl) {
        statusEl.textContent = 'Ошибка сети';
        statusEl.className = 'task-status task-status-error';
      }
    }
  };

  // Функция для вставки символов в поле ввода
  const insertSymbol = (blockIndex: number, symbol: string) => {
    console.log('[CalibrationPage] insertSymbol вызван для блока', blockIndex, 'с символом', symbol);
    const input = document.querySelector<HTMLInputElement>(`#answer_${blockIndex}`);
    if (!input) {
      console.warn('[CalibrationPage] Поле ввода для блока', blockIndex, 'не найдено');
      return;
    }
    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const val = input.value;
    input.value = val.substring(0, start) + symbol + val.substring(end);
    input.selectionStart = input.selectionEnd = start + symbol.length;
    input.focus();
  };

  // Функция для обработки клика по кнопке "i"
  const toggleInfo = (element: HTMLElement) => {
    console.log('[CalibrationPage] toggleInfo вызван');
    const block = element.closest('.processed_qblock');
    block?.classList.toggle('show-info');
  };

  // Функция для переключения видимости математических кнопок
  const toggleMathButtons = (element: HTMLElement) => {
    console.log('[CalibrationPage] toggleMathButtons вызван');
    const block = element.closest('.processed_qblock');
    const mathButtons = block?.querySelector('.math-buttons');
    mathButtons?.classList.toggle('active');
  };

  // Обработчик отправки формы ответа
  const submitAnswerAndCheck = (e: React.FormEvent, blockIndex: string) => {
    console.log('[CalibrationPage] submitAnswerAndCheck вызван для блока', blockIndex);
    e.preventDefault();
    const taskBlock = blocks.find(block => block.blockIndex === blockIndex);
    if (taskBlock) {
      handleSubmit(e, taskBlock.taskId, taskBlock.formId, taskBlock.blockIndex);
    } else {
      console.warn('[CalibrationPage] Блок для submitAnswerAndCheck не найден:', blockIndex);
    }
  };

  useEffect(() => {
    console.log('[CalibrationPage] Запуск useEffect добавления обработчиков, loading:', loading, 'blocks.length:', blocks.length);
    if (loading || blocks.length === 0) {
      console.log('[CalibrationPage] Условие для добавления обработчиков не выполнено, выходим из useEffect');
      return;
    }

    // 3) Проверяем и инициализируем MathJax
    if (window.MathJax && window.MathJax.Hub) {
      console.log('[CalibrationPage] Инициализация MathJax');
      try {
        window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub]);
        console.log('[CalibrationPage] Команда Typeset отправлена в очередь MathJax');
      } catch (mathJaxErr) {
        console.error('[CalibrationPage] Ошибка при вызове MathJax.Hub.Queue:', mathJaxErr);
      }
    } else {
      console.warn('[CalibrationPage] window.MathJax или window.MathJax.Hub не найден');
    }

    // 4) Определяем window.insertSymbol
    console.log('[CalibrationPage] Определение window.insertSymbol');
    window.insertSymbol = insertSymbol;

    // 2) После рендеринга HTML добавляем обработчики
    // Используем setTimeout, чтобы дать React время обновить DOM
    setTimeout(() => {
      console.log('[CalibrationPage] setTimeout для добавления обработчиков запущен');

      // Обработчики для кнопок "i"
      console.log('[CalibrationPage] Поиск .info-button');
      const infoButtons = document.querySelectorAll<HTMLElement>('.info-button');
      console.log('[CalibrationPage] Найдено .info-button:', infoButtons.length);
      infoButtons.forEach(btn => {
        console.log('[CalibrationPage] Обработка .info-button, data-handled:', btn.hasAttribute('data-handled'));
        if (!btn.hasAttribute('data-handled')) {
          btn.setAttribute('data-handled', 'true');
          // 1) Привязываем обработчик напрямую, не полагаясь на `this`
          btn.addEventListener('click', function(e) {
            e.preventDefault(); // Предотвращаем возможное выполнение встроенных обработчиков
            toggleInfo(this); // Передаем `this` (элемент кнопки)
          });
        } else {
          console.log('[CalibrationPage] .info-button уже имеет обработчик');
        }
      });

      // Обработчики для кнопок переключения математических символов
      console.log('[CalibrationPage] Поиск .toggle-math-btn');
      const mathToggleButtons = document.querySelectorAll<HTMLElement>('.toggle-math-btn');
      console.log('[CalibrationPage] Найдено .toggle-math-btn:', mathToggleButtons.length);
      mathToggleButtons.forEach(btn => {
        console.log('[CalibrationPage] Обработка .toggle-math-btn, data-handled:', btn.hasAttribute('data-handled'));
        if (!btn.hasAttribute('data-handled')) {
          btn.setAttribute('data-handled', 'true');
          btn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleMathButtons(this);
          });
        } else {
          console.log('[CalibrationPage] .toggle-math-btn уже имеет обработчик');
        }
      });

      // Обработчики для кнопок "Ответить" в старых формах (ссылки)
      console.log('[CalibrationPage] Поиск .answer-button (старые формы)');
      const answerButtons = document.querySelectorAll<HTMLElement>('.answer-button');
      console.log('[CalibrationPage] Найдено .answer-button:', answerButtons.length);
      answerButtons.forEach(btn => {
        console.log('[CalibrationPage] Обработка .answer-button, data-handled:', btn.hasAttribute('data-handled'));
        if (!btn.hasAttribute('data-handled')) {
          btn.setAttribute('data-handled', 'true');
          btn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('[CalibrationPage] Клик по старой кнопке ответа');
            const panel = btn.closest('.answer-panel');
            const form = panel?.previousElementSibling as HTMLFormElement;
            if (form && form.name === 'chkcodeform') {
              // Найти поле ввода в следующем sibling - новой форме .answer-form
              const newForm = panel?.nextElementSibling as HTMLFormElement;
              const input = newForm?.querySelector('input[name="answer"]');
              const statusDiv = newForm?.nextElementSibling as HTMLDivElement; // task-status

              if (input) {
                const block = btn.closest('.processed_qblock');
                const blockIndex = block?.id?.replace('processed_qblock_', '');
                if (blockIndex) {
                  // Имитируем отправку новой формы
                  const submitEvent = new Event('submit', { cancelable: true });
                  // @ts-ignore - добавляем кастомное свойство
                  submitEvent.blockIndex = blockIndex;
                  newForm?.dispatchEvent(submitEvent);
                }
              }
            }
          });
        } else {
          console.log('[CalibrationPage] .answer-button уже имеет обработчик');
        }
      });

      // Обработчики для новых форм с onsubmit
      console.log('[CalibrationPage] Поиск .answer-form с onsubmit');
      const newAnswerForms = document.querySelectorAll<HTMLFormElement>('.answer-form');
      console.log('[CalibrationPage] Найдено .answer-form:', newAnswerForms.length);
      newAnswerForms.forEach(form => {
        console.log('[CalibrationPage] Обработка .answer-form, data-handled:', form.hasAttribute('data-handled'));
        if (!form.hasAttribute('data-handled')) {
          form.setAttribute('data-handled', 'true');
          form.addEventListener('submit', function(e: Event) { // Изменяем тип на Event
            e.preventDefault();
            console.log('[CalibrationPage] Submit новой формы');
            // Получаем blockIndex из атрибута onsubmit
            const onSubmitAttr = form.getAttribute('onsubmit');
            if (onSubmitAttr) {
              const match = onSubmitAttr.match(/submitAnswerAndCheck\(event,\s*(\d+)\)/);
              if (match) {
                const blockIndex = match[1];
                console.log('[CalibrationPage] Извлечен blockIndex из onsubmit:', blockIndex);
                const taskBlock = blocks.find(b => b.blockIndex === blockIndex);
                if (taskBlock) {
                  // Явно приводим e к React.FormEvent через unknown
                  handleSubmit(e as unknown as React.FormEvent, taskBlock.taskId, taskBlock.formId, taskBlock.blockIndex);
                } else {
                  console.warn('[CalibrationPage] Блок не найден для blockIndex из onsubmit:', blockIndex);
                }
              } else {
                console.error('[CalibrationPage] Не удалось извлечь blockIndex из onsubmit:', onSubmitAttr);
              }
            } else {
              console.error('[CalibrationPage] Атрибут onsubmit не найден в .answer-form');
            }
          });
        } else {
          console.log('[CalibrationPage] .answer-form уже имеет обработчик');
        }
      });

    }, 100); // Небольшая задержка для полного рендеринга DOM React'ом

  }, [blocks, loading]); // 5) Зависимости остались прежними

  if (loading) {
    console.log('[CalibrationPage] Отображение состояния загрузки');
    return <div style={{ padding: '20px', textAlign: 'center' }}>Загрузка заданий...</div>;
  }

  console.log('[CalibrationPage] Рендеринг компонента, количество блоков:', blocks.length);
  return (
    <div className="container">
      <header>
        <h1>Калибровка навыков</h1>
        <button
          onClick={() => navigate('/math')}
          style={{
            marginTop: '10px',
            padding: '8px 16px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Назад к выбору
        </button>
      </header>
      <main>
        {blocks.length === 0 ? (
          <div>Не удалось загрузить задания</div>
        ) : (
          blocks.map((block) => (
            <div
              key={block.taskId}
              className="task-block-wrapper"
              dangerouslySetInnerHTML={{ __html: block.html }}
            />
          ))
        )}
      </main>
    </div>
  );
};

export default CalibrationPage;
