import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

// Глобальные типы для MathJax и insertSymbol
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

const TestBlockPage: React.FC = () => {
  const { problemId } = useParams<{ problemId: string }>();
  const [block, setBlock] = useState<TaskBlock | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!problemId) {
      navigate('/math');
      return;
    }

    const loadBlock = async () => {
      try {
        const res = await fetch(`/api/v1/block/${problemId}`);
        if (!res.ok) {
          console.error(`Ошибка загрузки блока для problem_id ${problemId}`);
          return;
        }
        const html = await res.text();
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const qblock = tempDiv.querySelector('.processed_qblock');
        const taskId = qblock?.getAttribute('data-task-id') || problemId;
        const formId = qblock?.getAttribute('data-form-id') || '';
        setBlock({ html, taskId, formId, blockIndex: problemId });
      } catch (err) {
        console.error('Ошибка загрузки блока:', err);
      } finally {
        setLoading(false);
      }
    };

    loadBlock();
  }, [problemId, navigate]);

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
    if (loading || !block) return;

    if (window.MathJax && window.MathJax.Hub) {
      window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub]);
    }

    window.insertSymbol = (blockIndex: string, symbol: string) => {
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
          const blockEl = btn.closest('.processed_qblock');
          blockEl?.classList.toggle('show-info');
        });
      }
    });

    document.querySelectorAll<HTMLFormElement>('.answer-form').forEach(form => {
      if (!form.hasAttribute('data-handled')) {
        form.setAttribute('data-handled', 'true');
        form.addEventListener('submit', (e) => {
          e.preventDefault();
          const blockEl = form.closest('.processed_qblock');
          const blockIndex = blockEl?.getAttribute('data-task-id');
          if (blockIndex) {
            const taskId = blockIndex;
            const formId = blockEl?.getAttribute('data-form-id') || '';
            handleSubmit(e as unknown as React.FormEvent, taskId, formId, blockIndex);
          }
        });
      }
    });
  }, [block, loading]);

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Загрузка задания...</div>;
  }

  if (!block) {
    return <div>Задание не найдено</div>;
  }

  return (
    <div className="container">
      <header>
        <h1>Тест одного задания</h1>
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
        <div
          dangerouslySetInnerHTML={{ __html: block.html }}
        />
      </main>
    </div>
  );
};

export default TestBlockPage;
