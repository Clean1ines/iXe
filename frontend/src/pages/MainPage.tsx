import React from 'react';
import { useNavigate } from 'react-router-dom';

const MainPage: React.FC = () => {
  const navigate = useNavigate();
  const handleMathClick = () => {
    navigate('/math');
  };
  const handleStubClick = (subject: string) => {
    alert(`Раздел "${subject}" пока недоступен.`);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '600px', margin: '0 auto' }}>
      <h1>Подготовка к ЕГЭ</h1>
      <p>Выберите предмет:</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
        <button
          onClick={handleMathClick}
          style={{
            padding: '14px',
            fontSize: '18px',
            backgroundColor: '#1976d2',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
          }}
        >
          Математика (Профильный Уровень)
        </button>
        <button
          onClick={() => handleStubClick('Информатика')}
          style={{
            padding: '14px',
            fontSize: '18px',
            backgroundColor: '#9e9e9e',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'not-allowed',
          }}
          disabled
        >
          Информатика
        </button>
        <button
          onClick={() => handleStubClick('Русский язык')}
          style={{
            padding: '14px',
            fontSize: '18px',
            backgroundColor: '#9e9e9e',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'not-allowed',
          }}
          disabled
        >
          Русский язык
        </button>
      </div>
    </div>
  );
};

export default MainPage;
