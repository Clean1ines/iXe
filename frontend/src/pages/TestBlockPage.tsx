import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

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

const TestBlockPage: React.FC = () => {
  const blockContainerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const loadAndDisplayBlock = async () => {
      if (!blockContainerRef.current) return;

      setError(null); // Сброс ошибки перед новой попыткой загрузки
      setLoading(true);

      // 1. Извлечение problem_id из query-параметра
      const problemId = searchParams.get('problem_id');
      if (!problemId) {
        setError('Не указан параметр problem_id в URL.');
        setLoading(false);
        return;
      }

      try {
        // 2. Fetch фрагмента блока с бэкенд-сервера через API
        console.log(`Загружаем блок для problem_id: ${problemId}`);
        const res = await fetch(`/api/v1/block/${problemId}`);

        if (!res.ok) {
          if (res.status === 404) {
            setError(`Задача с ID ${problemId} не найдена.`);
          } else {
            setError(`Ошибка загрузки блока: ${res.status} ${res.statusText}`);
          }
          setLoading(false);
          return;
        }

        const htmlFragment = await res.text();

        // 3. Очистить контейнер и вставить фрагмент
        blockContainerRef.current.innerHTML = ''; // Очищаем перед вставкой
        blockContainerRef.current.innerHTML = htmlFragment; // Вставляем HTML

        // 4. Инициализировать MathJax для нового содержимого (если он подключен)
        if (window.MathJax && window.MathJax.Hub) {
          window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub, blockContainerRef.current]);
        } else {
          console.warn('MathJax не найден на window. Формулы могут не отобразиться.');
        }

        // 5. Определить глобальные функции, если они не определены (например, insertSymbol)
        // Используем логику из CalibrationPage
        window.insertSymbol = (blockIndex: number, symbol: string) => {
          const input = document.querySelector<HTMLInputElement>(`#answer_${blockIndex}`);
          if (!input) return;
          const start = input.selectionStart || 0;
          const end = input.selectionEnd || 0;
          const val = input.value;
          input.value = val.substring(0, start) + symbol + val.substring(end);
          input.selectionStart = input.selectionEnd = start + symbol.length;
          input.focus();
        };

        // 6. Привязать обработчики событий к вставленным элементам
        // Используем логику из CalibrationPage с добавлением атрибута data-handled
        document.querySelectorAll('.info-button').forEach(btn => {
          if (!btn.hasAttribute('data-handled')) {
            btn.setAttribute('data-handled', 'true');
            btn.addEventListener('click', () => {
              const block = btn.closest('.processed_qblock');
              block?.classList.toggle('show-info');
            });
          }
        });

        document.querySelectorAll('.toggle-math-btn').forEach(btn => {
          if (!btn.hasAttribute('data-handled')) {
            btn.setAttribute('data-handled', 'true');
            btn.addEventListener('click', () => {
              const block = btn.closest('.processed_qblock');
              const mathButtons = block?.querySelector('.math-buttons');
              mathButtons?.classList.toggle('active');
            });
          }
        });

        // Обработчик формы
        const answerForm = blockContainerRef.current.querySelector<HTMLFormElement>('.answer-form');
        if (answerForm && !answerForm.hasAttribute('data-handled')) {
          answerForm.setAttribute('data-handled', 'true');
          answerForm.addEventListener('submit', function(e: Event) {
            e.preventDefault();
            const onSubmitAttr = answerForm.getAttribute('onsubmit');
            if (onSubmitAttr) {
              // Извлекаем blockIndex (в данном случае это будет problemId) из строки submitAnswerAndCheck(event, 'problemId')
              const match = onSubmitAttr.match(/submitAnswerAndCheck\(event,\s*["']([^"']+)["']\)/);
              if (match) {
                const blockIndexStr = match[1];
                // Извлекаем taskId и formId из атрибутов .processed_qblock
                const qblock = answerForm.closest('.processed_qblock');
                const taskId = qblock?.getAttribute('data-task-id') || 'unknown';
                const formId = qblock?.getAttribute('data-form-id') || '';

                // Вызываем handleSubmit, имитируя логику из CalibrationPage
                // Поскольку у нас один блок, мы можем определить handleSubmit локально
                const handleSubmit = async (
                  e: React.FormEvent,
                  taskId: string,
                  formId: string,
                  blockIndex: string
                ) => {
                  e.preventDefault();
                  const input = document.querySelector<HTMLInputElement>(`#answer_${blockIndex}`);
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
                    const res = await fetch('/answer', { // Используем прокси
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ problem_id: taskId, user_answer: userAnswer, form_id: formId }),
                    });
                    const data = await res.json();
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
                    console.error('Ошибка:', err);
                    if (statusEl) {
                      statusEl.textContent = 'Ошибка сети';
                      statusEl.className = 'task-status task-status-error';
                    }
                  }
                };

                handleSubmit(e as unknown as React.FormEvent, taskId, formId, blockIndexStr);
              } else {
                console.error(`Не удалось извлечь blockIndex из onsubmit: ${onSubmitAttr}`);
              }
            } else {
              console.error('Атрибут onsubmit не найден в .answer-form');
            }
          });
        }

        console.log('Блок успешно загружен и вставлен.');
      } catch (err) {
        console.error('Ошибка в TestBlockPage:', err);
        setError('Произошла ошибка при загрузке или обработке блока.');
      } finally {
        setLoading(false);
      }
    };

    loadAndDisplayBlock();
  }, [searchParams]); // Зависимость от searchParams, чтобы перезагружать при изменении параметра

  return (
    <div className="container">
      <header>
        <h1>Тестовый Блок</h1>
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
        {loading && <div style={{ padding: '20px', textAlign: 'center' }}>Загрузка задания...</div>}
        {error && <div style={{ padding: '20px', color: 'red', textAlign: 'center' }}>{error}</div>}
        <div ref={blockContainerRef} id="test-block-container">
          {/* Блок будет вставлен сюда */}
        </div>
      </main>
    </div>
  );
};

export default TestBlockPage;
