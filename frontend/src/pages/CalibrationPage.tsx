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
        // Получаем 10 случайных problem_id через новый эндпоинт
        // Предполагаем, что эндпоинт /subjects/problems/random?count=10 уже реализован
        // или эмулируем его через /subjects/available и фильтрацию на фронте
        // Для начала получим доступные задачи по математике
        const subject = 'math'; // или другой выбранный предмет
        const count = 10;
        // Эмулируем вызов эндпоинта, который возвращает список всех problem_id для subject
        // const allProblemsRes = await fetch(`/subjects/${subject}/problems`);
        // const allProblemsData = await allProblemsRes.json();
        // const allProblemIds = allProblemsData.problem_ids || [];
        // const shuffled = allProblemIds.sort(() => 0.5 - Math.random());
        // const selectedProblemIds = shuffled.slice(0, count);

        // Пока используем эмуляцию через /subjects/available + фильтрация на фронте
        // Предполагаем, что задачи имеют формат {subject}_XXXXXX
        const availableSubjectsRes = await fetch('/api/v1/subjects/available');
        const availableSubjectsData = await availableSubjectsRes.json();
        const availableSubjects = availableSubjectsData.subjects || [];

        if (!availableSubjects.includes(subject)) {
          throw new Error(`Subject ${subject} not available`);
        }

        // Предположим, что у нас есть эндпоинт для получения задач по предмету
        // const subjectProblemsRes = await fetch(`/api/v1/subjects/${subject}/problems`);
        // const subjectProblemsData = await subjectProblemsRes.json();
        // const allProblemIds = subjectProblemsData.problem_ids || [];

        // Так как эндпоинта пока нет, эмулируем получение списка задач из БД
        // Для этого создадим временный эндпоинт или используем обходной путь
        // Пока просто сгенерируем тестовые ID или получим их через другой способ
        // Используем заглушку для получения списка задач по предмету
        // Допустим, есть эндпоинт /subjects/{subject}/all_problems
        const allSubjectProblemsRes = await fetch(`/api/v1/subjects/${subject}/all_problems`);
        let allSubjectProblemsData = { problem_ids: [] };
        if (allSubjectProblemsRes.ok) {
          allSubjectProblemsData = await allSubjectProblemsRes.json();
        } else {
          console.warn("Не удалось получить список задач по предмету, используем fallback.");
          // Fallback: попробуем получить все задачи и отфильтровать
          const allProblemsRes = await fetch('/api/v1/problems'); // Предполагаем, что такой эндпоинт есть
          if (allProblemsRes.ok) {
            const allProblemsData = await allProblemsRes.json();
            allSubjectProblemsData.problem_ids = allProblemsData.problems.filter((p: any) => p.subject === subject).map((p: any) => p.problem_id);
          } else {
            console.error("Не удалось получить список задач.");
            return;
          }
        }
        const allProblemIds = allSubjectProblemsData.problem_ids || [];

        if (allProblemIds.length === 0) {
          console.warn(`Нет доступных задач для предмета ${subject}.`);
          return;
        }

        const shuffled = allProblemIds.sort(() => 0.5 - Math.random());
        const selectedProblemIds = shuffled.slice(0, count);

        const loadedBlocks: TaskBlock[] = [];

        for (const problemId of selectedProblemIds) {
          const res = await fetch(`/api/v1/block/${problemId}`);
          if (!res.ok) {
            console.error(`Ошибка загрузки блока для problem_id ${problemId}:`, res.status, res.statusText);
            continue;
          }
          const html = await res.text();
          const tempDiv = document.createElement('div');
          tempDiv.innerHTML = html;
          const qblock = tempDiv.querySelector('.processed_qblock');
          // taskId и formId извлекаются из атрибутов .processed_qblock
          // которые должны быть сгенерированы на бэкенде
          const taskId = qblock?.getAttribute('data-task-id') || 'unknown';
          const formId = qblock?.getAttribute('data-form-id') || '';
          // blockIndex теперь будем использовать problemId
          const blockIndex = problemId;
          loadedBlocks.push({ html, taskId, formId, blockIndex });
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
      const res = await fetch('/answer', { // Теперь используем прокси
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
