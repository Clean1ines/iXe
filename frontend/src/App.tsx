import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainPage from './pages/MainPage';
import MathPage from './pages/MathPage';
import CalibrationPage from './pages/CalibrationPage'; // текущая страница
import TestBlockPage from './pages/TestBlockPage'; // новая тестовая страница

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/math" element={<MathPage />} />
        <Route path="/math/calibrate" element={<CalibrationPage />} />
        <Route path="/math/test-block" element={<TestBlockPage />} /> {/* Добавлен маршрут */}
      </Routes>
    </BrowserRouter>
  );
};

export default App;
