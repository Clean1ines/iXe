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
  blockIndex: string; // Сохраняем как строку
}

const CalibrationPage: React.FC = () => {
  const [blocks, setBlocks] = useState<TaskBlock[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const loadRandomBlocks = async () => {
      try {
        // --- НАЧАЛО: Динамическое определение totalCount ---
        let filenames: string[] = [];
        let totalCount = 0;
        let max_Y_from_list = -1;
        let max_Y = -1; // <-- ВЫНЕСЛИ ОБЪЯВЛЕНИЕ СЮДА

        try {
          const listFileRes = await fetch('/blocks/math/blocks_list.json');
          if (listFileRes.ok) {
            const listData = await listFileRes.json();
            filenames = listData.files || [];
            totalCount = filenames.length;
            max_Y_from_list = listData.max_Y || -1;
            console.log(`Найдено ${totalCount} файлов блоков из blocks_list.json.`);
          }
        } catch (listErr) {
          console.warn("Не удалось загрузить blocks_list.json, пробуем эвристику.");
        }

        if (totalCount === 0) {
          let max_X = -1;
          let foundInit = false;
          for (let x = 0; x <= 20; x++) {
            const initCheckRes = await fetch(`/blocks/math/block_${x}_init.html`);
            if (initCheckRes.ok) {
              foundInit = true;
              max_X = Math.max(max_X, x);
            } else {
              break;
            }
          }

          if (max_X >= 0) {
            for (let y = 1; y <= 100; y++) {
              const yCheckRes = await fetch(`/blocks/math/block_${max_X}_${y}.html`);
              if (yCheckRes.ok) {
                max_Y = y; // <-- ИСПОЛЬЗУЕМ УЖЕ ОБЪЯВЛЁННУЮ ПЕРЕМЕННУЮ
              } else {
                break;
              }
            }
          }

          if (foundInit && max_Y >= 0) {
            totalCount = (max_X + 1) * (max_Y + 1);
            console.log(`Оценённый totalCount на основе max_X=${max_X}, max_Y=${max_Y}: ${totalCount}`);
          } else {
            console.error("Не удалось определить диапазон файлов. Используем fallback.");
            totalCount = 1;
          }
        }
        // --- КОНЕЦ: динамическое определение totalCount ---

        if (totalCount === 0) {
          console.error("totalCount не удалось определить, прерываем загрузку.");
          return;
        }

        const allIds = Array.from({ length: totalCount }, (_, i) => i);
        const shuffled = allIds.sort(() => 0.5 - Math.random());
        const selectedIds = shuffled.slice(0, 10);

        const loadedBlocks: TaskBlock[] = [];

        for (const id of selectedIds) {
          if (filenames.length > 0 && id < filenames.length) {
            const filename = filenames[id];
            const res = await fetch(`/blocks/math/${filename}`);
            if (!res.ok) {
              console.error(`Ошибка загрузки блока ${filename} (id ${id}):`, res.status, res.statusText);
              continue;
            }
            const html = await res.text();
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const qblock = tempDiv.querySelector('.processed_qblock');
            const taskId = qblock?.getAttribute('data-task-id') || 'unknown';
            const formId = qblock?.getAttribute('data-form-id') || '';
            const blockIndex = filename.replace('block_', '').replace('.html', '');
            loadedBlocks.push({ html, taskId, formId, blockIndex });
          } else {
            // Используем max_Y, объявленный выше
            const max_Y_evaluated = max_Y_from_list >= 0 ? max_Y_from_list : (max_Y >= 0 ? max_Y : 97);
            const N = max_Y_evaluated + 1;
            const X = Math.floor(id / N);
            const remainder = id % N;
            let filename;
            if (remainder === 0) {
              filename = `block_${X}_init.html`;
            } else {
              filename = `block_${X}_${remainder}.html`;
            }

            const res = await fetch(`/blocks/math/${filename}`);
            if (!res.ok) {
              console.error(`Ошибка загрузки блока ${filename} (id ${id}, X=${X}, rem=${remainder}):`, res.status, res.statusText);
              continue;
            }
            const html = await res.text();
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const qblock = tempDiv.querySelector('.processed_qblock');
            const taskId = qblock?.getAttribute('data-task-id') || 'unknown';
            const formId = qblock?.getAttribute('data-form-id') || '';
            const blockIndex = filename.replace('block_', '').replace('.html', '');
            loadedBlocks.push({ html, taskId, formId, blockIndex });
          }
        }
        setBlocks(loadedBlocks);
      } catch (err) {
        console.error('Ошибка загрузки блоков:', err);
      } finally {
        setLoading(false);
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
      const res = await fetch('https://ixe-core.onrender.com/answer', {
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

  useEffect(() => {
    if (loading || blocks.length === 0) return;

    if (window.MathJax && window.MathJax.Hub) {
      window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub]);
    }

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

    document.querySelectorAll<HTMLFormElement>('.answer-form').forEach(form => {
      if (!form.hasAttribute('data-handled')) {
        form.setAttribute('data-handled', 'true');
        form.addEventListener('submit', function(e: Event) {
          e.preventDefault();
          const onSubmitAttr = form.getAttribute('onsubmit');
          if (onSubmitAttr) {
            const match = onSubmitAttr.match(/submitAnswerAndCheck\(event,\s*["']([^"']+)["']\)/);
            if (!match) {
              const matchNum = onSubmitAttr.match(/submitAnswerAndCheck\(event,\s*(\d+)\)/);
              if (matchNum) {
                console.warn("Обнаружен старый формат onsubmit, ожидается строка. Проверьте шаблон.");
                const blockIndexNum = matchNum[1];
                const taskBlock = blocks.find(b => b.blockIndex === blockIndexNum);
                if (taskBlock) {
                  handleSubmit(e as unknown as React.FormEvent, taskBlock.taskId, taskBlock.formId, taskBlock.blockIndex);
                } else {
                  console.error(`Блок с blockIndex ${blockIndexNum} не найден в состоянии blocks.`);
                }
              } else {
                console.error(`Не удалось извлечь blockIndex из onsubmit: ${onSubmitAttr}`);
              }
            } else {
              const blockIndexStr = match[1];
              const taskBlock = blocks.find(b => b.blockIndex === blockIndexStr);
              if (taskBlock) {
                handleSubmit(e as unknown as React.FormEvent, taskBlock.taskId, taskBlock.formId, taskBlock.blockIndex);
              } else {
                console.error(`Блок с blockIndex ${blockIndexStr} не найден в состоянии blocks.`);
              }
            }
          } else {
            console.error('Атрибут onsubmit не найден в .answer-form');
          }
        });
      }
    });
  }, [blocks, loading]);

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Загрузка заданий...</div>;
  }

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
              dangerouslySetInnerHTML={{ __html: block.html }}
            />
          ))
        )}
      </main>
    </div>
  );
};

export default CalibrationPage;