import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const TestBlockPage: React.FC = () => {
  const blockContainerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadAndDisplayBlock = async () => {
      if (!blockContainerRef.current) return;

      try {
        // 1. Fetch фрагмента блока с фронтенд-сервера
        // Используем тот же подход, что и в CalibrationPage, но для одного блока
        // Предположим, что файл block_6_init.html соответствует задаче 71BC43
        // (Это нужно проверить вручную, но для теста подставим правильный ID)
        // В CalibrationPage: blockIndex = qblock?.id?.replace('processed_qblock_', '') || id.toString();
        // и id = 6, значит файл block_6_init.html
        // В файле block_6_init.html: id="processed_qblock_6", data-task-id="71BC43"
        // Значит, чтобы протестировать задачу 71BC43, нужно запросить block_6_init.html
        // Найдём файл, соответствующий task-id 71BC43
        // Из примера CalibrationPage: const blockIndex = qblock?.id?.replace('processed_qblock_', '') || id.toString();
        // Это означает, что id внутри файла (processed_qblock_N) определяет имя файла (block_N_...html).
        // Мы не знаем это id заранее по task-id.
        // Лучший способ - это сгенерировать список файлов и сопоставить task-id с именем файла.
        // Пока что, используем известное сопоставление из примера.
        const targetTaskId = '71BC43';
        // Предположим, файл block_6_init.html содержит задачу 71BC43 (как в примере CalibrationPage)
        // Это нужно будет автоматизировать позже.
        // Попробуем загрузить block_6_init.html
        const blockFileName = 'block_6_init.html'; // Заменить на правильный файл для 71BC43
        console.log(`Загружаем блок из файла: /blocks/math/${blockFileName}`);
        const res = await fetch(`/blocks/math/${blockFileName}`);
        if (!res.ok) {
          console.error(`Ошибка загрузки блока из файла ${blockFileName}: ${res.status} ${res.statusText}`);
          return;
        }
        const htmlFragment = await res.text();

        // 2. Извлечь фрагмент <div class="processed_qblock"> из полученного HTML-фрагмента
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlFragment, 'text/html');
        const qblockFragment = doc.querySelector('.processed_qblock');

        if (!qblockFragment) {
          console.error('Фрагмент .processed_qblock не найден в полученном HTML-фрагменте');
          return;
        }

        // Проверим, совпадает ли task-id в извлеченном фрагменте с целевым
        const taskIdInFragment = qblockFragment.getAttribute('data-task-id');
        if (taskIdInFragment !== targetTaskId) {
            console.warn(`Предупреждение: task-id в файле (${taskIdInFragment}) не совпадает с целевым (${targetTaskId}). Продолжаем с тем, что есть.`);
        } else {
            console.log(`Найден блок для задачи ${taskIdInFragment}`);
        }

        // 3. Очистить контейнер и вставить фрагмент
        blockContainerRef.current.innerHTML = ''; // Очищаем перед вставкой
        blockContainerRef.current.appendChild(qblockFragment);

        // 4. Инициализировать MathJax для нового содержимого (если он подключен)
        if ((window as any).MathJax && (window as any).MathJax.Hub) {
          (window as any).MathJax.Hub.Queue(['Typeset', (window as any).MathJax.Hub, blockContainerRef.current]);
        } else {
          console.warn('MathJax не найден на window. Формулы могут не отобразиться.');
        }

        // 5. Определить глобальные функции, если они не определены (например, insertSymbol)
        if (typeof (window as any).insertSymbol !== 'function') {
          (window as any).insertSymbol = (blockIndex: number, symbol: string) => {
            const input = document.querySelector<HTMLInputElement>(`#answer_${blockIndex}`);
            if (!input) return;
            const start = input.selectionStart || 0;
            const end = input.selectionEnd || 0;
            const val = input.value;
            input.value = val.substring(0, start) + symbol + val.substring(end);
            input.selectionStart = input.selectionEnd = start + symbol.length;
            input.focus();
          };
        }

        // 6. Привязать обработчики событий к вставленным элементам (если они не сработали из HTML)
        // Пример для кнопки "i"
        const infoButton = blockContainerRef.current.querySelector('.info-button');
        if (infoButton) {
          infoButton.addEventListener('click', (e) => {
            e.preventDefault();
            const block = infoButton.closest('.processed_qblock');
            block?.classList.toggle('show-info');
          });
        }

        // Пример для кнопки математических символов
        const mathToggleBtn = blockContainerRef.current.querySelector('.toggle-math-btn');
        if (mathToggleBtn) {
          mathToggleBtn.addEventListener('click', () => {
            const block = mathToggleBtn.closest('.processed_qblock');
            const mathButtons = block?.querySelector('.math-buttons');
            mathButtons?.classList.toggle('active');
          });
        }

        // Пример для формы ответа (если onsubmit не сработал)
        const answerForm = blockContainerRef.current.querySelector('.answer-form') as HTMLFormElement;
        if (answerForm) {
          const onSubmitAttr = answerForm.getAttribute('onsubmit');
          if (onSubmitAttr) {
            // Извлекаем blockIndex из строки submitAnswerAndCheck(event, X)
            // Для block_6_init.html blockIndex должен быть '6'
            const match = onSubmitAttr.match(/submitAnswerAndCheck\(event,\s*(\d+)\)/);
            if (match) {
              const blockIndex = parseInt(match[1], 10);
              console.log(`Найден blockIndex: ${blockIndex} для формы`);
              answerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                console.log(`Форма отправлена для blockIndex: ${blockIndex}, taskId: ${taskIdInFragment}`);
                // Здесь можно вызвать вашу логику отправки ответа, например, handleSubmit
                // handleSubmit(e, taskIdInFragment, formId, blockIndex);
              });
            } else {
                console.error(`Не удалось извлечь blockIndex из onsubmit: ${onSubmitAttr}`);
            }
          } else {
              console.error('Атрибут onsubmit не найден в .answer-form');
          }
        }

        console.log('Блок успешно загружен и вставлен.');
      } catch (err) {
        console.error('Ошибка в TestBlockPage:', err);
      }
    };

    loadAndDisplayBlock();
  }, []);

  return (
    <div className="container">
      <header>
        <h1>Тестовый Блок Страница (71BC43)</h1>
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
        <div ref={blockContainerRef} id="test-block-container">
          {/* Блок будет вставлен сюда */}
        </div>
      </main>
    </div>
  );
};

export default TestBlockPage;
