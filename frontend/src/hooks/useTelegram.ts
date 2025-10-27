import { useState, useEffect } from 'react';
import bridge from '@vkontakte/vk-bridge';

interface TelegramUser {
  id: number;
  first_name: string;
  last_name: string;
  username: string;
  language_code: string;
}

interface UseTelegramReturn {
  tgUser: TelegramUser | null;
  isTelegram: boolean;
  sendNotification: ((type: 'success' | 'error' | 'warning') => void) | null;
  closeApp: (() => void) | null;
}

/**
 * Хук для работы с Telegram Web Apps API через VK Bridge
 * Проверяет, запущено ли приложение в Telegram, получает информацию о пользователе
 * @returns Объект с информацией о пользователе, статусе Telegram и методами взаимодействия
 */
export const useTelegram = (): UseTelegramReturn => {
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null);
  
  // Проверяем, запущено ли приложение в Telegram WebView
  const isTelegram = bridge.isWebView() || !!(window as any).Telegram?.WebApp;

  useEffect(() => {
    if (isTelegram) {
      // Получаем информацию о пользователе
      bridge
        .send('VKWebAppGetUserInfo')
        .then((data: any) => {
          setTgUser({
            id: data.id,
            first_name: data.first_name,
            last_name: data.last_name,
            username: data.username,
            language_code: data.language_code
          });
        })
        .catch((error: any) => {
          console.error('Ошибка получения информации о пользователе:', error);
        });
    }
  }, [isTelegram]);

  /**
   * Отправляет уведомление о тактильной обратной связи в Telegram
   * @param type - тип уведомления ('success', 'error', 'warning')
   */
  const sendNotification = isTelegram
    ? (type: 'success' | 'error' | 'warning'): void => {
        bridge.send('VKWebAppTapticNotificationOccurred', { type });
      }
    : null;

  /**
   * Закрывает Telegram Mini App
   */
  const closeApp = isTelegram
    ? (): void => {
        bridge.send('VKWebAppClose', { status: 'success' });
      }
    : null;

  return {
    tgUser,
    isTelegram,
    sendNotification,
    closeApp
  };
};
