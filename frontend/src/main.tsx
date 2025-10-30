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

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
