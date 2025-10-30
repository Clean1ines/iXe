import React from 'react';
import { useNavigate } from 'react-router-dom';

const MainPage: React.FC = () => {
  const navigate = useNavigate();

  const handleStartQuiz = () => {
    navigate('/quiz');
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Подготовка к ЕГЭ</h1>
      <p>Выберите предмет и начните решать задачи.</p>
      <button onClick={handleStartQuiz}>Начать тест</button>
    </div>
  );
};

export default MainPage;
