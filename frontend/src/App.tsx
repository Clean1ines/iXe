import React from 'react';
import { Routes, Route } from 'react-router-dom';
import QuizPage from './pages/QuizPage';
import HomePage from './pages/HomePage';

/**
 * Главный компонент приложения
 * Обеспечивает маршрутизацию для Telegram Mini App
 */
const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/quiz/:pageName" element={<QuizPage />} />
    </Routes>
  );
};

export default App;
