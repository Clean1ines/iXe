import React from 'react';
import { Problem } from '../types';

// Временные данные — 5 задач по профильной математике
const mockProblems: Problem[] = [
  {
    id: '1',
    subject: 'math',
    question: 'Решите уравнение: \\( x^2 - 5x + 6 = 0 \\)',
    correctAnswer: '2;3',
  },
  {
    id: '2',
    subject: 'math',
    question: 'Найдите производную функции \\( f(x) = 3x^4 - 2x + 7 \\)',
    correctAnswer: '12x^3 - 2',
  },
  {
    id: '3',
    subject: 'math',
    question: 'Чему равен \\( \\log_2 8 \\)?',
    correctAnswer: '3',
  },
  {
    id: '4',
    subject: 'math',
    question: 'В треугольнике ABC угол C прямой, AC = 3, BC = 4. Найдите AB.',
    correctAnswer: '5',
  },
  {
    id: '5',
    subject: 'math',
    question: 'Решите неравенство: \\( 2x - 5 > 3 \\)',
    correctAnswer: 'x > 4',
  },
];

const QuizPage: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '700px', margin: '0 auto' }}>
      <h2>Математика (Профильный Уровень)</h2>
      <p>Решите задачи:</p>
      <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {mockProblems.map((problem) => (
          <div
            key={problem.id}
            style={{
              padding: '16px',
              border: '1px solid #ddd',
              borderRadius: '8px',
              backgroundColor: '#f9f9f9',
            }}
          >
            <div
              dangerouslySetInnerHTML={{
                __html: `<p><strong>Задача ${problem.id}:</strong> ${problem.question}</p>`,
              }}
            />
            {/* В будущем здесь будет <AnswerForm problemId={problem.id} /> */}
          </div>
        ))}
      </div>
    </div>
  );
};

export default QuizPage;
