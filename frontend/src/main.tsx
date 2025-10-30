import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Для Telegram Mini Apps: проверяем наличие window.Telegram.WebApp
if (typeof window !== 'undefined' && (window as any).Telegram?.WebApp) {
  console.log('Running inside Telegram Mini App');
  // Можно инициализировать Telegram WebApp здесь, если нужно
  const WebApp = (window as any).Telegram.WebApp;
  WebApp.ready();
}

// Подключаем MathJax из CDN
const script = document.createElement('script');
script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML';
script.async = true;
document.head.appendChild(script);

// Опционально: добавляем обработчик на загрузку MathJax
script.onload = () => {
  console.log('MathJax loaded');
};

// Добавляем обработчик глобальных ошибок
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  console.error('Error message:', event.message);
  console.error('Error source:', event.filename);
  console.error('Error line:', event.lineno);
  console.error('Error column:', event.colno);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
