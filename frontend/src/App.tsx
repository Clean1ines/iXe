// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainPage from './pages/MainPage';
import MathPage from './pages/MathPage'; // новая страница

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/math" element={<MathPage />} />
        {/* В будущем: /informatics, /russian */}
      </Routes>
    </BrowserRouter>
  );
};

export default App;