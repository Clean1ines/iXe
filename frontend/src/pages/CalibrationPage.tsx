import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

declare global {
  interface Window {
    MathJax?: {
      Hub: {
        Queue: (args: any[]) => void;
      };
    };
    insertSymbol?: (blockIndex: string, symbol: string) => void;
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
    const loadRandomBlocks = async () => {
      try {
        const subject = 'math';
        const count = 10;

        const res = await fetch(`/api/v1/subjects/${subject}/random_problems?count=${count}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const problemIds: string[] = data.problem_ids;

        if (problemIds.length === 0) {
          setBlocks([]);
          return;
        }

        const loadedBlocks: TaskBlock[] = [];
        for (const problemId of problemIds) {
          const blockRes = await fetch(`/api/v1/block/${problemId}`);
          if (!blockRes.ok) continue;
          const html = await blockRes.text();
          const tempDiv = document.createElement('div');
          tempDiv.innerHTML = html;
          const qblock = tempDiv.querySelector('.processed_qblock');
          const taskId = qblock?.getAttribute('data-task-id') || problemId;
          const formId = qblock?.getAttribute('data-form-id') || '';
          loadedBlocks.push({ html, taskId, formId, blockIndex: problemId });
        }
        setBlocks(loadedBlocks);
      } catch (err) {
        console.error('Ошибка загрузки блоков:', err);
        setBlocks([]);
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
      const res = await fetch('/answer', {
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

    if (window.MathJax?.Hub) {
      window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub]);
    }

    window.insertSymbol = (blockIndex, symbol) => {
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
          btn.closest('.processed_qblock')?.classList.toggle('show-info');
        });
      }
    });

    document.querySelectorAll('.answer-form').forEach(form => {
      if (!form.hasAttribute('data-handled')) {
        form.setAttribute('data-handled', 'true');
        form.addEventListener('submit', (e) => {
          e.preventDefault();
          const block = form.closest('.processed_qblock');
          const blockIndex = block?.getAttribute('data-task-id');
          if (blockIndex) {
            const taskId = blockIndex;
            const formId = block?.getAttribute('data-form-id') || '';
            handleSubmit(e as unknown as React.FormEvent, taskId, formId, blockIndex);
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
              key={block.blockIndex}
              dangerouslySetInnerHTML={{ __html: block.html }}
            />
          ))
        )}
      </main>
    </div>
  );
};

export default CalibrationPage;
