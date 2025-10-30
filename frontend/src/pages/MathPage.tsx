import React from 'react';
import { useNavigate } from 'react-router-dom';

const MathPage: React.FC = () => {
  const navigate = useNavigate();
  const handleCalibrate = () => {
    navigate('/math/calibrate');
  };
  const handleContinue = () => {
    alert('Продолжить подготовку — пока недоступно');
  };
  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Математика (Профильный Уровень)</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
        <button
          onClick={handleCalibrate}
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
          Калибровка навыков
        </button>
        <button
          onClick={handleContinue}
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
          Продолжить подготовку
        </button>
        <button
          onClick={() => navigate('/')}
          style={{
            padding: '14px',
            fontSize: '18px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
          }}
        >
          Вернуться в главное меню
        </button>
      </div>
    </div>
  );
};

export default MathPage;
