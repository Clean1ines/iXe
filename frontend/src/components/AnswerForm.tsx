import React, { useState, useEffect } from 'react';
import { submitAnswer } from '../utils/api';
import { getAnswerLocally, saveAnswerLocally } from '../utils/db';
import { CheckAnswerResponse } from '../types/api';

interface AnswerFormProps {
  problemId: string;
  formId: string;
  onCorrectAnswer?: () => void;
}

/**
 * Форма для ввода ответа на задачу
 * @param problemId - идентификатор задачи
 * @param formId - идентификатор формы
 * @param onCorrectAnswer - колбэк, вызываемый при правильном ответе
 */
const AnswerForm: React.FC<AnswerFormProps> = ({ problemId, formId, onCorrectAnswer }) => {
  const [userAnswer, setUserAnswer] = useState('');
  const [status, setStatus] = useState<'correct' | 'incorrect' | 'pending'>('pending');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Загружаем локально сохранённый ответ при монтировании
    const saved = getAnswerLocally(problemId);
    if (saved.answer) {
      setUserAnswer(saved.answer);
      setStatus(saved.status as 'correct' | 'incorrect' | 'pending');
    }
  }, [problemId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response: CheckAnswerResponse = await submitAnswer({
        quiz_id: 'current_quiz', // будет обновлено в реальной реализации
        problem_id: problemId,
        user_answer: userAnswer,
        form_id: formId
      });

      setStatus(response.verdict === 'correct' ? 'correct' : 'incorrect');
      
      // Сохраняем ответ и статус локально
      saveAnswerLocally(problemId, userAnswer, response.verdict);
      
      if (response.verdict === 'correct' && onCorrectAnswer) {
        onCorrectAnswer();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
      setStatus('pending');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSymbol = (symbol: string) => {
    setUserAnswer(prev => prev + symbol);
  };

  const getStatusClass = () => {
    if (status === 'correct') return 'status-correct';
    if (status === 'incorrect') return 'status-incorrect';
    return 'status-pending';
  };

  return (
    <form onSubmit={handleSubmit} id={formId} className="answer-form">
      <div className="input-container">
        <input
          type="text"
          value={userAnswer}
          onChange={(e) => setUserAnswer(e.target.value)}
          placeholder="Введите ответ"
          disabled={loading || status === 'correct'}
          className={getStatusClass()}
        />
        <div className="symbol-buttons">
          <button type="button" onClick={() => handleAddSymbol('√')} disabled={loading}>√</button>
          <button type="button" onClick={() => handleAddSymbol('π')} disabled={loading}>π</button>
          <button type="button" onClick={() => handleAddSymbol('^')} disabled={loading}>^</button>
          <button type="button" onClick={() => handleAddSymbol('/')} disabled={loading}>/</button>
        </div>
      </div>
      <button type="submit" disabled={loading || status === 'correct'}>
        {loading ? 'Проверка...' : status === 'correct' ? 'Правильно!' : 'Ответить'}
      </button>
      {error && <div className="error-message">{error}</div>}
      {status !== 'pending' && (
        <div className={`status-message ${getStatusClass()}`}>
          {status === 'correct' ? '✓ Правильно!' : '✗ Неправильно'}
        </div>
      )}
    </form>
  );
};

export default AnswerForm;
