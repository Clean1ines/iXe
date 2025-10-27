import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ProblemBlock from '../components/ProblemBlock';
import { startDailyQuiz } from '../utils/api';
import { useTelegram } from '../hooks/useTelegram';
import { QuizItem } from '../types/api';

/**
 * Страница квиза, отображающая задачи для решения
 * Получает pageName из URL и загружает соответствующие задачи
 */
const QuizPage: React.FC = () => {
  const { pageName } = useParams<{ pageName: string }>();
  const [quizItems, setQuizItems] = useState<QuizItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { sendNotification } = useTelegram(); // Убрали неиспользуемую переменную tgUser

  useEffect(() => {
    const loadQuiz = async () => {
      try {
        setLoading(true);
        const response = await startDailyQuiz(pageName);
        setQuizItems(response.items);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
        setLoading(false);
      }
    };

    loadQuiz();
  }, [pageName]);

  if (loading) {
    return <div>Загрузка...</div>;
  }

  if (error) {
    return <div>Ошибка: {error}</div>;
  }

  return (
    <div className="quiz-page">
      <h1>Квиз: {pageName || 'Ежедневный'}</h1>
      {quizItems.map(item => (
        <ProblemBlock 
          key={item.problem_id} 
          item={item} 
          onCorrectAnswer={() => {
            if (sendNotification) {
              sendNotification('success');
            }
          }}
        />
      ))}
    </div>
  );
};

export default QuizPage;
