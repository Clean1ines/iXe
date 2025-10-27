import React from 'react';
import { Routes, Route } from 'react-router-dom';
import QuizPage from './pages/QuizPage';
import MainPage from './pages/MainPage'; // NEW: Import MainPage

/**
 * Главный компонент приложения
 * Обеспечивает маршрутизацию для Telegram Mini App
 */
const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} /> {/* NEW: Route to MainPage */}
      <Route path="/quiz/:pageName" element={<QuizPage />} />
    </Routes>
  );
};

export default App;
