/**
 * Сохраняет ответ пользователя локально
 * @param taskId - идентификатор задачи
 * @param answer - текст ответа пользователя
 * @param status - статус ответа ('correct', 'incorrect', 'pending')
 */
export function saveAnswerLocally(taskId: string, answer: string, status: string): void {
  const key = `answer_${taskId}`;
  const data = {
    answer,
    status,
    timestamp: Date.now()
  };
  localStorage.setItem(key, JSON.stringify(data));
}

/**
 * Получает локально сохранённый ответ для задачи
 * @param taskId - идентификатор задачи
 * @returns Объект с ответом и статусом, или null если не найдено
 */
export function getAnswerLocally(taskId: string): { answer: string | null; status: string } {
  const key = `answer_${taskId}`;
  const stored = localStorage.getItem(key);

  if (stored) {
    try {
      const data = JSON.parse(stored);
      return {
        answer: data.answer || null,
        status: data.status || 'pending'
      };
    } catch (e) {
      console.error('Ошибка при чтении локального ответа:', e);
      return { answer: null, status: 'pending' };
    }
  }

  return { answer: null, status: 'pending' };
}

/**
 * Возвращает все локально сохранённые ответы
 * @returns Объект с ключами taskId и значениями { answer, status }
 */
export function getAllLocalAnswers(): Record<string, { answer: string; status: string }> {
  const answers: Record<string, { answer: string; status: string }> = {};
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith('answer_')) {
      const taskId = key.substring(7); // 'answer_'.length
      const stored = localStorage.getItem(key);
      if (stored) {
        try {
          const data = JSON.parse(stored);
          answers[taskId] = {
            answer: data.answer,
            status: data.status
          };
        } catch (e) {
          console.error('Ошибка при чтении локального ответа:', e);
        }
      }
    }
  }
  return answers;
}

/**
 * Обновляет статус локально сохранённого ответа
 * @param taskId - идентификатор задачи
 * @param status - новый статус ответа
 */
export function updateStatusLocally(taskId: string, status: string): void {
  const key = `answer_${taskId}`;
  const stored = localStorage.getItem(key);

  if (stored) {
    try {
      const data = JSON.parse(stored);
      data.status = status;
      data.timestamp = Date.now();
      localStorage.setItem(key, JSON.stringify(data));
    } catch (e) {
      console.error('Ошибка при обновлении статуса локального ответа:', e);
    }
  } else {
    // Если запись не существует, создаём новую с пустым ответом
    saveAnswerLocally(taskId, '', status);
  }
}

/**
 * Очищает все локально сохранённые ответы
 */
export function clearAllLocalAnswers(): void {
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('answer_')) {
      localStorage.removeItem(key);
    }
  });
}
