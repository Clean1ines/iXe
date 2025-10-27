import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Стартовая страница приложения
 * Предоставляет выбор предмета для начала квиза
 */
const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedSubject, setSelectedSubject] = useState<string>('init'); // По умолчанию 'init'

  const subjects = [
    { value: 'init', label: 'ЕГЭ Математика' },
    { value: 'physics', label: 'ЕГЭ Физика' },
    { value: 'informatics', label: 'ЕГЭ Информатика' },
    // Добавь другие предметы по мере их добавления
  ];

  const handleStartQuiz = () => {
    navigate(`/quiz/${selectedSubject}`);
  };

  return (
    <div className="home-page">
      <h1>Добро пожаловать в Quiz App</h1>
      <p>Выберите предмет для начала квиза:</p>
      
      <div className="subject-selector">
        <select 
          value={selectedSubject} 
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="subject-dropdown"
        >
          {subjects.map(subject => (
            <option key={subject.value} value={subject.value}>
              {subject.label}
            </option>
          ))}
        </select>
        
        <button onClick={handleStartQuiz} className="start-button">
          Начать квиз
        </button>
      </div>
    </div>
  );
};

export default HomePage;
