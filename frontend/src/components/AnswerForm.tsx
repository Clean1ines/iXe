import React, { useState } from 'react';

interface AnswerFormProps {}

const AnswerForm: React.FC<AnswerFormProps> = () => {
  const [answer, setAnswer] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Отправлен ответ:', answer);
    // Здесь будет логика отправки и проверки
  };

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="user-answer">Ваш ответ:</label>
      <input
        id="user-answer"
        type="text"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        placeholder="Введите ответ"
        style={{ display: 'block', marginTop: '8px', padding: '6px', width: '200px' }}
      />
      <button type="submit" style={{ marginTop: '12px' }}>
        Проверить
      </button>
    </form>
  );
};

export default AnswerForm;
